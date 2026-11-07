"""
FIR-MINT v4: Fast Incremental Re-Tuning for multi-vector index configurations.

Experiments
  E1  Measured (FAISS HNSW) latency/recall after abrupt drift: Static vs FIR vs Full re-tune,
      plus tuning cost (what-if calls, wall-clock, new index builds), over several seeds.
  E2  Scalability: tuning cost and solution quality as the number of vector columns grows.
  E3  Timeline: four drift scenarios (abrupt, gradual, recurring, new query type) with the
      online detector (sustained-drift + cooldown) driving re-tuning.

Design
  * MINT-style estimators: per-plan latency and recall are calibrated once from real FAISS
    measurements, then the tuners query only the estimators ("what-if calls"), so the
    configuration choice is deterministic and not driven by timing noise.
  * Planner: for each query type, choose the cheapest plan (exact multi-column index,
    partial cover such as (T,I)+(M), or merge of single-column indexes) that meets the
    recall target.
  * Objective: lexicographic (probability mass of query types violating recall, expected cost),
    under a storage budget.
  * Full re-tune: greedy search from scratch over every multi-column type seen in the workload.
    FIR: warm start from the current configuration, drop unused indexes, and consider only the
    top-K most frequent new types.
  * Drift detector: KL(window || reference) with smoothing, threshold from a parametric bootstrap
    (mean + 3 std), sustained-drift rule (2 consecutive windows) and cooldown.
v4 changes
  * Equal-recall plans: merge plans widen their candidate pool (40..640) until the calibrated
    recall meets the target, so stale configurations pay in latency instead of silently
    violating recall.
  * Benefit-aware, adaptive FIR candidates: each potential index is scored by its estimated
    gain per storage unit on the query types it can serve (exact or as a 2+1 partial cover);
    the candidate count adapts to capture 80% of the total positive gain (3..8).
  * What-if cache shared by both tuners: a plan is re-estimated only when an index relevant
    to that query type changes; only cache misses count as what-if calls.
Dependencies: numpy, matplotlib, faiss-cpu
"""
import itertools, json, os, time
from pathlib import Path
import numpy as np
import faiss
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

faiss.omp_set_num_threads(1)

N, DIM, TOP_K, POOL = 10000, 48, 10, 40
HNSW_M, EF_CONS, EF_SEARCH = 32, 128, 256
LATENT, NOISE = 0.5, 0.3
RECALL_TARGET, MAXQ = 0.90, 3
EXTRA_BUDGET = 8          # storage for multi-column indexes, in single-column units
FIR_KMIN, FIR_KMAX, FIR_COVER = 3, 8, 0.8
POOLS = (40, 80, 160, 320, 640, 1280, 2560)
WIN = 300                 # queries per monitoring window
SEEDS = [0, 1, 2, 3, 4]
USE_CACHE = True
BUILD_THREADS = int(os.environ.get("FIR_BUILD_THREADS", "1"))
REAL, REAL_Q, _REAL_STORE = None, None, []   # set by --data (real embeddings)
OUT = Path("fir_mint_v4_results"); OUT.mkdir(exist_ok=True)


# ---------------------------------------------------------------- utilities
def normalize(x):
    return x / np.maximum(np.linalg.norm(x, axis=-1, keepdims=True), 1e-12)


def types_for(C):
    return [q for m in range(1, MAXQ + 1) for q in itertools.combinations(range(C), m)]


def gen_data(C, rng):
    if REAL is not None:
        return REAL[:C]
    lat = rng.normal(size=(N, DIM))
    return [normalize(LATENT * lat + (1 - LATENT) * rng.normal(size=(N, DIM))).astype(np.float32)
            for _ in range(C)]


def zipf_dist(C, rng, single_mass, exp=1.1, zero=()):
    T = types_for(C)
    singles = [q for q in T if len(q) == 1]
    multi = [q for q in T if len(q) > 1 and q not in zero]
    p = {q: 0.0 for q in T}
    for q, w in zip(singles, rng.dirichlet(np.ones(len(singles)) * 4)):
        p[q] = single_mass * w
    w = 1 / np.arange(1, len(multi) + 1) ** exp
    w /= w.sum()
    for r, i in enumerate(rng.permutation(len(multi))):
        p[multi[i]] = (1 - single_mass) * w[r]
    return p


def mix(p, q, a):
    return {k: (1 - a) * p[k] + a * q[k] for k in p}


def sample_window(p, rng, n=WIN):
    keys = list(p)
    counts = rng.multinomial(n, np.array([p[k] for k in keys]))
    return {k: c / n for k, c in zip(keys, counts)}


def kl(p, q, eps=1e-3):
    keys = list(p)
    a = np.array([p[k] for k in keys]) + eps
    b = np.array([q[k] for k in keys]) + eps
    a, b = a / a.sum(), b / b.sum()
    return float(np.sum(a * np.log(a / b)))


# ---------------------------------------------------------------- FAISS layer
def get_store(data):
    """Synthetic: fresh store per seed. Real data: one shared store (indexes reused across seeds)."""
    if REAL is None:
        return Store(data)
    if not _REAL_STORE:
        _REAL_STORE.append(Store(REAL))
    return _REAL_STORE[0]


class Store:
    """Cache of built HNSW indexes with their build times."""

    def __init__(self, data):
        self.data, self.idx, self.build_s = data, {}, {}

    def get(self, key):
        if key not in self.idx:
            t0 = time.perf_counter()
            v = np.ascontiguousarray(normalize(np.hstack([self.data[c] for c in key])), dtype=np.float32)
            unique_ratio = np.unique(v, axis=0).shape[0] / len(v)
            if len(key) == 1 and unique_ratio < 0.99:
                ix = faiss.IndexFlatIP(v.shape[1])
            else:
                ix = faiss.IndexHNSWFlat(v.shape[1], HNSW_M, faiss.METRIC_INNER_PRODUCT)
                ix.hnsw.efConstruction = EF_CONS
            faiss.omp_set_num_threads(BUILD_THREADS)
            try:
                ix.add(v)
            finally:
                faiss.omp_set_num_threads(1)
            if hasattr(ix, "hnsw"):
                ix.hnsw.efSearch = EF_SEARCH
            self.idx[key], self.build_s[key] = ix, time.perf_counter() - t0
        return self.idx[key]


def make_query(data, q, rng):
    if REAL_Q is not None:                         # held-out real rows (e.g. COCO val2017)
        r = int(rng.integers(0, len(REAL_Q[0])))
        return {c: REAL_Q[c][r] for c in q}
    r = int(rng.integers(0, N))
    return {c: normalize(data[c][r] + NOISE * rng.normal(size=DIM).astype(np.float32) / np.sqrt(DIM)) for c in q}


def joint(data, q, qv, ids=None):
    rows = slice(None) if ids is None else ids
    return sum(data[c][rows] @ qv[c] for c in q) / len(q)


def topk(s, k):
    k = min(k, len(s))
    i = np.argpartition(-s, k - 1)[:k]
    return i[np.argsort(-s[i])]


def ann(ix, vec, k):
    if hasattr(ix, "hnsw"):
        ix.hnsw.efSearch = max(EF_SEARCH, k)
    _, I = ix.search(np.ascontiguousarray(vec[None], dtype=np.float32), k)
    return I[0][I[0] >= 0]


def run_plan(store, plan, q, qv):
    kind, parts, pool = plan
    t0 = time.perf_counter()
    if kind == "exact":
        res = ann(store.get(q), normalize(np.concatenate([qv[c] for c in q])), TOP_K)
    else:
        cand = np.unique(np.concatenate(
            [ann(store.get(p), normalize(np.concatenate([qv[c] for c in p])), pool) for p in parts]))
        res = cand[topk(joint(store.data, q, qv, cand), TOP_K)]
    return res, (time.perf_counter() - t0) * 1000


def recall_of(store, q, plan, qv):
    got, _ = run_plan(store, plan, q, qv)
    scores = joint(store.data, q, qv)
    boundary = np.partition(scores, -TOP_K)[-TOP_K]
    tolerance = max(1e-6, abs(float(boundary)) * 1e-6)
    relevant = np.flatnonzero(scores >= boundary - tolerance)
    denominator = min(TOP_K, len(relevant))
    return min(1.0, len(set(got) & set(relevant)) / denominator)


# ---------------------------------------------------------------- estimators + planner
class Estimator:
    """Calibrated once from real FAISS measurements on a 3-column store (columns exchangeable).
    For each merge signature, the smallest pool that meets the recall target is recorded."""

    def __init__(self, store, rng, n=150):
        d = store.data
        self.lat = {}

        Cn = len(d)

        def rand_q(m):
            return tuple(sorted(rng.choice(Cn, size=m, replace=False).tolist()))

        def time_ann(s, k):
            ts = []
            for _ in range(n):
                key = rand_q(s); ix = store.get(key)
                qv = make_query(d, key, rng)
                vec = normalize(np.concatenate([qv[c] for c in key]))
                t0 = time.perf_counter(); ann(ix, vec, k); ts.append(time.perf_counter() - t0)
            return float(np.median(ts)) * 1000

        for s_ in (1, 2, 3):
            self.lat[(s_, TOP_K)] = time_ann(s_, TOP_K)
        ts = []
        for _ in range(n):
            qv = make_query(d, (0, 1, 2), rng)
            ids = rng.integers(0, N, size=2 * POOL)
            t0 = time.perf_counter(); joint(d, (0, 1, 2), qv, ids); ts.append(time.perf_counter() - t0)
        self.rerank_per = float(np.median(ts)) * 1000 / (2 * POOL * 3)

        self.rec = {}
        for m in (1, 2, 3):
            qs = [rand_q(m) for _ in range(n)]
            self.rec[("exact", m)] = float(np.min(
                [recall_of(store, q, ("exact", None, None), make_query(d, q, rng)) for q in qs]))
        self.mpool = {}
        def parts_for(sig, q):
            return [(c,) for c in q] if sig != (2, 1) else [q[:2], q[2:]]

        for sig in ((1, 1), (1, 1, 1), (2, 1)):
            qq = [rand_q(len(sig) if sig != (2, 1) else 3) for _ in range(n)]
            qs = [(q, make_query(d, q, rng)) for q in qq]
            for pool in POOLS:
                r = float(np.min([recall_of(store, q, ("merge", parts_for(sig, q), pool), qv)
                                  for q, qv in qs]))
                if r >= RECALL_TARGET or pool == POOLS[-1]:
                    break
            self.mpool[sig], self.rec[sig] = pool, r
            for s_ in set(sig):
                if (s_, pool) not in self.lat:
                    self.lat[(s_, pool)] = time_ann(s_, pool)
        self.calls, self.cache = 0, {}

    def merge_cost(self, sig, m):
        pool = self.mpool[sig]
        return sum(self.lat[(s_, pool)] for s_ in sig) + self.rerank_per * len(sig) * pool * m

    def plans(self, q, cfg):
        m = len(q)
        if m == 1 or q in cfg:
            yield ("exact", None, None), self.lat[(m, TOP_K)], self.rec[("exact", m)]
        if m > 1:
            sig = (1,) * m
            yield ("merge", [(c,) for c in q], self.mpool[sig]), self.merge_cost(sig, m), self.rec[sig]
        if m == 3:
            for s_ in itertools.combinations(q, 2):
                if s_ in cfg:
                    rest = tuple(c for c in q if c not in s_)
                    yield (("merge", [s_, rest], self.mpool[(2, 1)]), self.merge_cost((2, 1), 3),
                           self.rec[(2, 1)])

    def best_plan(self, q, cfg):
        rel = frozenset(i for i in cfg if i == q or (len(q) == 3 and len(i) == 2 and set(i) < set(q)))
        key = (q, rel)
        if not USE_CACHE:
            self.cache.pop(key, None)
        if key not in self.cache:
            self.calls += 1
            opts = list(self.plans(q, rel))
            ok = [o for o in opts if o[2] >= RECALL_TARGET]
            self.cache[key] = min(ok, key=lambda o: o[1]) if ok else max(opts, key=lambda o: o[2])
        return self.cache[key]

    def score(self, dist, cfg):
        viol = cost = 0.0
        for q, p in dist.items():
            if p <= 0:
                continue
            _, c, r = self.best_plan(q, cfg)
            cost += p * c
            if r < RECALL_TARGET:
                viol += p
        return round(viol, 9), cost


def served_by(i, dist):
    return sum(p for q, p in dist.items() if q == i or (len(q) == 3 and len(i) == 2 and set(i) < set(q)))


def candidate_universe(dist):
    seen = {q for q, p in dist.items() if len(q) > 1 and p > 0}
    for q in list(seen):
        if len(q) == 3:
            seen |= set(itertools.combinations(q, 2))
    return sorted(seen)


def storage(cfg):
    return sum(len(i) for i in cfg)


def greedy(est, dist, cfg, candidates):
    cfg = frozenset(cfg)
    best = est.score(dist, cfg)
    while True:
        trials = [(est.score(dist, cfg | {c}), c) for c in candidates
                  if c not in cfg and storage(cfg | {c}) <= EXTRA_BUDGET]
        if not trials:
            return cfg, best
        s, c = min(trials, key=lambda t: t[0])
        if s >= best:
            return cfg, best
        cfg, best = cfg | {c}, s


def full_retune(est, dist, current=frozenset()):
    est.calls, est.cache = 0, {}; t0 = time.perf_counter()
    cands = candidate_universe(dist)
    cfg, s = greedy(est, dist, frozenset(), cands)
    return cfg, s, est.calls, time.perf_counter() - t0


def fir_retune(est, dist, current):
    """Warm-start local search from the current configuration: drop moves and add-and-repair
    moves (add a candidate, evict least-valuable indexes to fit the budget)."""
    est.calls, est.cache = 0, {}; t0 = time.perf_counter()
    cfg = frozenset(current)
    # Benefit-aware candidates: estimated gain of adding each index alone, scored only on the
    # query types it can serve, divided by its storage. Keep the smallest top set that captures
    # FIR_COVER of the total positive gain (bounded by FIR_KMIN..FIR_KMAX).
    gains = []
    for i in candidate_universe(dist):
        if i in cfg:
            continue
        sub = {q: p for q, p in dist.items() if p > 0 and (q == i or (len(q) == 3 and set(i) < set(q)))}
        v0, c0 = est.score(sub, cfg)
        v1, c1 = est.score(sub, cfg | {i})
        g = (v0 - v1) * 10.0 + (c0 - c1)          # recall violations dominate cost
        if g > 0:
            gains.append((g / len(i), i))
    gains.sort(reverse=True)
    total = sum(g for g, _ in gains)
    cands, acc = [], 0.0
    for g, i in gains:
        if len(cands) >= FIR_KMAX or (len(cands) >= FIR_KMIN and acc >= FIR_COVER * total):
            break
        cands.append(i); acc += g
    def repair(c):
        """Add c, then evict the indexes whose removal hurts least until the budget fits."""
        m = cfg | {c}
        while storage(m) > EXTRA_BUDGET:
            m = min((m - {i} for i in m if i != c), key=lambda x: est.score(dist, x))
        return m

    best = est.score(dist, cfg)
    while True:
        moves = [cfg - {i} for i in cfg]                                   # drop
        moves += [repair(c) for c in cands if c not in cfg]                # add (+ evict to fit)
        if not moves:
            break
        scored = [(est.score(dist, m), m) for m in moves]
        s_, m = min(scored, key=lambda t: (t[0], storage(t[1])))
        if s_ > best or (s_ == best and storage(m) >= storage(cfg)):
            break
        cfg, best = m, s_
    return cfg, best, est.calls, time.perf_counter() - t0


# ---------------------------------------------------------------- drift detector
class Detector:
    def __init__(self, ref, rng, sustain=2, cooldown=2):
        self.rng, self.sustain, self.cooldown = rng, sustain, cooldown
        self.reset(ref)

    def reset(self, ref):
        self.ref, self.hits, self.cool, self.buf = ref, 0, self.cooldown, []
        sm = {k: v + 1e-3 for k, v in ref.items()}
        tot = sum(sm.values()); sm = {k: v / tot for k, v in sm.items()}
        s = [kl(sample_window(sm, self.rng), sample_window(sm, self.rng)) for _ in range(300)]
        self.thr = float(np.mean(s) + 3 * np.std(s))

    def observe(self, win):
        """Returns the pooled histogram to re-tune on, or None."""
        if self.cool > 0:
            self.cool -= 1
            return None
        if kl(win, self.ref) > self.thr:
            self.hits += 1; self.buf.append(win)
        else:
            self.hits, self.buf = 0, []
        if self.hits >= self.sustain:
            pooled = {k: np.mean([w[k] for w in self.buf]) for k in win}
            return pooled
        return None


# ---------------------------------------------------------------- E1: measured comparison
def e1(C=4):
    rows = []
    for seed in SEEDS:
        rng = np.random.default_rng(seed)
        data = gen_data(C, rng)
        store = get_store(data)
        est = Estimator(store, rng)
        p0 = zipf_dist(C, rng, single_mass=0.85)
        p1 = zipf_dist(C, rng, single_mass=0.35)
        static, _, _, _ = full_retune(est, sample_window(p0, rng))
        for i in static: store.get(i)
        obs = {k: (a + b) / 2 for (k, a), b in zip(sample_window(p1, rng).items(), sample_window(p1, rng).values())}
        fir, _, fir_calls, fir_t = fir_retune(est, obs, static)
        full, _, full_calls, full_t = full_retune(est, obs)

        keys = list(p1)
        test = [keys[i] for i in rng.choice(len(keys), 600, p=[p1[k] for k in keys])]
        qvs = [make_query(data, q, rng) for q in test]
        pols = [("Static", static, 0, 0.0), ("FIR-MINT", fir, fir_calls, fir_t),
                ("Full re-tune", full, full_calls, full_t)]
        plans, build = {}, {}
        for name, cfg, _, _ in pols:
            new = [i for i in cfg if i not in static]
            for i in cfg:
                store.get(i)
            build[name] = (len(new), sum(store.build_s[i] for i in new))
            plans[name] = [est.best_plan(q, cfg)[0] for q in test]
        lat = {name: [] for name, *_ in pols}
        for rnd in range(4):                       # round 0 = warm-up
            order = pols[rnd % 3:] + pols[:rnd % 3]
            for name, *_ in order:
                ts = [run_plan(store, pl, q, qv)[1] for q, qv, pl in zip(test, qvs, plans[name])]
                if rnd > 0:
                    lat[name].append(ts)
        for name, cfg, calls, tt in pols:
            rec = {}
            for q, qv, pl in zip(test, qvs, plans[name]):
                rec.setdefault(q, []).append(recall_of(store, q, pl, qv))
            per_type = {q: np.mean(v) for q, v in rec.items()}
            viol = sum(p1[q] for q, r in per_type.items() if r < RECALL_TARGET)
            means = [np.mean(t) for t in lat[name]]
            allt = np.concatenate(lat[name])
            rows.append(dict(seed=seed, policy=name, latency_ms=float(np.median(means)),
                             p95_ms=float(np.percentile(allt, 95)),
                             min_recall=float(min(per_type.values())), viol_mass=float(viol),
                             whatif=calls, tune_s=tt, new_indexes=build[name][0], build_s=build[name][1],
                             storage=storage(cfg), config=[list(i) for i in sorted(cfg)]))
            print(f"[E1 seed {seed}] {name:12s} lat={rows[-1]['latency_ms']:.3f}ms "
                  f"minRec={rows[-1]['min_recall']:.3f} viol={viol:.3f} whatif={calls} new={build[name][0]} cfg={sorted(cfg)}")
    return rows


# ---------------------------------------------------------------- E2: scalability
def e2(Cs=(3, 4, 5, 6, 8, 10, 12)):
    rows = []
    for seed in SEEDS:
        rng = np.random.default_rng(100 + seed)
        est = Estimator(get_store(gen_data(3, rng)), rng, n=80)
        for C in Cs:
            p0 = zipf_dist(C, rng, 0.85); p1 = zipf_dist(C, rng, 0.35)
            static, *_ = full_retune(est, p0)
            obs = sample_window(p1, rng, n=2 * WIN)
            fir, _, fc, ft = fir_retune(est, obs, static)
            full, _, uc, ut = full_retune(est, obs)
            sv, sc = est.score(p1, static)
            fv, fcst = est.score(p1, fir)
            uv, ucst = est.score(p1, full)
            rows.append(dict(seed=seed, C=C, n_types=len(p1), fir_calls=fc, full_calls=uc,
                             fir_s=ft, full_s=ut, static_cost=sc, fir_cost=fcst, full_cost=ucst,
                             static_viol=sv, fir_viol=fv, full_viol=uv,
                             fir_new=len(fir - static), full_new=len(full - static)))
            print(f"[E2 seed {seed}] C={C:2d} types={len(p1):3d} whatif FIR={fc:6d} Full={uc:7d} "
                  f"cost static/FIR/full={sc:.3f}/{fcst:.3f}/{ucst:.3f} viol={sv:.2f}/{fv:.2f}/{uv:.2f}")
    return rows


# ---------------------------------------------------------------- E3: drift timelines
def scenario(name, C, rng, T=30):
    p0 = zipf_dist(C, rng, 0.85)
    p1 = zipf_dist(C, rng, 0.35)
    if name == "abrupt":
        return [p0 if t < 10 else p1 for t in range(T)], 10
    if name == "gradual":
        return [mix(p0, p1, min(1, max(0, (t - 10) / 10))) for t in range(T)], 10
    if name == "recurring":
        return [p0 if (t // 8) % 2 == 0 else p1 for t in range(T)], 8
    if name == "new_type":
        multi = [q for q in p0 if len(q) > 1]
        newq = multi[int(rng.integers(len(multi)))]
        base = zipf_dist(C, rng, 0.85, zero=(newq,))
        after = {k: v * 0.6 for k, v in base.items()}; after[newq] = 0.4
        return [base if t < 10 else after for t in range(T)], 10
    raise ValueError(name)


def e3(C=5, names=("abrupt", "gradual", "recurring", "new_type")):
    rows, traces = [], {}
    for seed in SEEDS:
        rng = np.random.default_rng(200 + seed)
        est = Estimator(get_store(gen_data(3, rng)), rng, n=80)
        for name in names:
            dists, onset = scenario(name, C, rng)
            init, *_ = full_retune(est, sample_window(dists[0], rng))
            res = {}
            for pol in ("Static", "FIR+detector", "Full+detector", "Full every window"):
                cfg, det = init, Detector(sample_window(dists[0], rng), rng)
                costs, viols, calls, builds, retunes, false_rt = [], [], 0, 0, [], 0
                for t, p in enumerate(dists):
                    v, c = est.score(p, cfg); costs.append(c); viols.append(v)
                    win = sample_window(p, rng)
                    if pol == "Static":
                        continue
                    if pol == "Full every window":
                        new, _, k, _ = full_retune(est, win, cfg)
                    else:
                        pooled = det.observe(win)
                        if pooled is None:
                            continue
                        fn = fir_retune if pol == "FIR+detector" else full_retune
                        new, _, k, _ = fn(est, pooled, cfg)
                        det.reset(pooled)
                        retunes.append(t)
                        if t < onset:
                            false_rt += 1
                    calls += k; builds += len(new - cfg); cfg = new
                res[pol] = costs
                rows.append(dict(seed=seed, scenario=name, policy=pol, mean_cost=float(np.mean(costs)),
                                 post_cost=float(np.mean(costs[onset:])), viol_mass=float(np.mean(viols)),
                                 whatif=calls, builds=builds, retunes=len(retunes), false_retunes=false_rt,
                                 first_retune=(min([t for t in retunes if t >= onset], default=None))))
            if seed == SEEDS[0]:
                traces[name] = (res, onset)
            print(f"[E3 seed {seed}] {name:9s} " + "  ".join(
                f"{r['policy']}: cost={r['mean_cost']:.3f} rt={r['retunes']} calls={r['whatif']}"
                for r in rows[-4:]))
    return rows, traces


# ---------------------------------------------------------------- reporting
def ms(v):
    return f"{np.mean(v):.3f} ± {np.std(v):.3f}"


def report(r1, r2, r3, traces):
    L = ["# FIR-MINT v4 results", "",
         f"Settings: N={N}, dim/column={DIM}, k={TOP_K}, pool={POOL}, HNSW M={HNSW_M}, efSearch={EF_SEARCH}, "
         f"recall target={RECALL_TARGET}, extra storage budget={EXTRA_BUDGET}, FIR candidates={FIR_KMIN}..{FIR_KMAX} (cover {FIR_COVER:.0%}), "
         f"window={WIN} queries, seeds={len(SEEDS)}. Values are mean ± std over seeds.", "",
         "## E1. Measured performance after abrupt drift (C=4, FAISS HNSW)", "",
         "| Policy | Latency (ms) | p95 (ms) | Min recall | Recall-violating mass | What-if calls | Tuning (s) | New indexes | Build (s) |",
         "|---|---|---|---|---|---|---|---|---|"]
    for pol in ("Static", "FIR-MINT", "Full re-tune"):
        R = [r for r in r1 if r["policy"] == pol]
        L.append(f"| {pol} | {ms([r['latency_ms'] for r in R])} | {ms([r['p95_ms'] for r in R])} | "
                 f"{ms([r['min_recall'] for r in R])} | {ms([r['viol_mass'] for r in R])} | "
                 f"{ms([r['whatif'] for r in R])} | {ms([r['tune_s'] for r in R])} | "
                 f"{ms([r['new_indexes'] for r in R])} | {ms([r['build_s'] for r in R])} |")
    L += [] if not r2 else ["", "## E2. Scalability (estimator-based, abrupt drift)", "",
          "| Columns | Query types | What-if FIR | What-if Full | Speed-up | Cost FIR/Full | Cost Static/Full | Viol FIR | Viol Full | Viol Static |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for C in sorted({r["C"] for r in r2}):
        R = [r for r in r2 if r["C"] == C]
        L.append(f"| {C} | {R[0]['n_types']} | {np.mean([r['fir_calls'] for r in R]):.0f} | "
                 f"{np.mean([r['full_calls'] for r in R]):.0f} | "
                 f"{np.mean([r['full_calls'] / r['fir_calls'] for r in R]):.1f}× | "
                 f"{ms([r['fir_cost'] / r['full_cost'] for r in R])} | {ms([r['static_cost'] / r['full_cost'] for r in R])} | "
                 f"{np.mean([r['fir_viol'] for r in R]):.3f} | {np.mean([r['full_viol'] for r in R]):.3f} | "
                 f"{np.mean([r['static_viol'] for r in R]):.3f} |")
    L += ["", f"## E3. Drift scenarios (C={E3_C}, 30 windows, estimator-based cost per window)", "",
          "| Scenario | Policy | Mean cost (ms) | Post-onset cost (ms) | Recall-violating mass | Re-tunes | False re-tunes | What-if calls | Index builds |",
          "|---|---|---|---|---|---|---|---|---|"]
    for sc in ("abrupt", "gradual", "recurring", "new_type"):
        for pol in ("Static", "FIR+detector", "Full+detector", "Full every window"):
            R = [r for r in r3 if r["scenario"] == sc and r["policy"] == pol]
            L.append(f"| {sc} | {pol} | {ms([r['mean_cost'] for r in R])} | {ms([r['post_cost'] for r in R])} | "
                     f"{ms([r['viol_mass'] for r in R])} | {ms([r['retunes'] for r in R])} | "
                     f"{ms([r['false_retunes'] for r in R])} | {np.mean([r['whatif'] for r in R]):.0f} | "
                     f"{np.mean([r['builds'] for r in R]):.1f} |")
    (OUT / "results.md").write_text("\n".join(L), encoding="utf-8")
    json.dump(dict(E1=r1, E2=r2, E3=r3), open(OUT / "results.json", "w"), indent=1, default=str)

    # Fig 1: E1 bars
    pols = ("Static", "FIR-MINT", "Full re-tune")
    fig, ax = plt.subplots(1, 3, figsize=(12, 3.6))
    for a, key, lab in zip(ax, ("latency_ms", "min_recall", "whatif"),
                           ("Mean latency (ms)", "Min per-type recall@10", "What-if calls")):
        vals = [[r[key] for r in r1 if r["policy"] == p] for p in pols]
        a.bar(pols, [np.mean(v) for v in vals], yerr=[np.std(v) for v in vals], capsize=4,
              color=["#9aa5b1", "#d9822b", "#2b6cb0"])
        a.set_title(lab); a.tick_params(axis="x", labelsize=8)
        if key == "min_recall":
            a.axhline(RECALL_TARGET, ls="--", c="k", lw=1); a.set_ylim(0.5, 1.02)
    fig.tight_layout(); fig.savefig(OUT / "fig1_measured.png", dpi=200); plt.close(fig)

    # Fig 2: scaling (synthetic only)
    if r2:
        Cs = sorted({r["C"] for r in r2})
        fig, ax = plt.subplots(1, 2, figsize=(11, 3.8))
        for key, lab, c in (("fir_calls", "FIR-MINT", "#d9822b"), ("full_calls", "Full re-tune", "#2b6cb0")):
            ax[0].plot(Cs, [np.mean([r[key] for r in r2 if r["C"] == C]) for C in Cs], marker="o", label=lab, c=c)
        ax[0].set_yscale("log"); ax[0].set_xlabel("Vector columns"); ax[0].set_ylabel("What-if calls (log)")
        ax[0].legend(); ax[0].set_title("Tuning effort")
        for key, lab, c in (("fir_cost", "FIR-MINT", "#d9822b"), ("static_cost", "Static", "#9aa5b1")):
            ax[1].plot(Cs, [np.mean([r[key] / r["full_cost"] for r in r2 if r["C"] == C]) for C in Cs],
                       marker="o", label=lab, c=c)
        ax[1].axhline(1, ls="--", c="#2b6cb0", label="Full re-tune")
        ax[1].set_xlabel("Vector columns"); ax[1].set_ylabel("Workload cost / Full"); ax[1].legend()
        ax[1].set_title("Solution quality")
        fig.tight_layout(); fig.savefig(OUT / "fig2_scaling.png", dpi=200); plt.close(fig)

    # Fig 3: timelines
    fig, ax = plt.subplots(2, 2, figsize=(12, 7), sharex=True)
    colors = {"Static": "#9aa5b1", "FIR+detector": "#d9822b", "Full+detector": "#2b6cb0",
              "Full every window": "#2f855a"}
    for a, sc in zip(ax.flat, ("abrupt", "gradual", "recurring", "new_type")):
        res, onset = traces[sc]
        for pol, cs in res.items():
            a.plot(cs, label=pol, c=colors[pol], lw=1.6, ls=":" if pol == "Full every window" else "-")
        a.axvline(onset, ls="--", c="k", lw=0.8); a.set_title(sc.replace("_", " "))
        a.set_ylabel("Est. cost (ms/query)")
    ax[1, 0].set_xlabel("Window"); ax[1, 1].set_xlabel("Window"); ax[0, 0].legend(fontsize=8)
    fig.tight_layout(); fig.savefig(OUT / "fig3_timelines.png", dpi=200); plt.close(fig)


E3_C = 5


def load_real(folder):
    global REAL, REAL_Q, N, DIM, OUT
    folder = Path(folder)
    cols = json.load(open(folder / "meta.json"))["columns"]
    REAL = [np.ascontiguousarray(np.load(folder / f"data_{c}.npy"), dtype=np.float32) for c in cols]
    REAL_Q = [np.ascontiguousarray(np.load(folder / f"query_{c}.npy"), dtype=np.float32) for c in cols]
    N, DIM = REAL[0].shape
    OUT = Path(f"fir_mint_v4_results_{folder.name}"); OUT.mkdir(exist_ok=True)
    print(f"Real data: {N} rows, {len(cols)} columns {cols}, dim={DIM}, {len(REAL_Q[0])} held-out queries")
    return len(cols)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", help="folder produced by coco_embed.py; omit for synthetic experiments")
    args = ap.parse_args()
    t = time.time()
    if args.data:
        C = load_real(args.data)
        E3_C = C
        r1 = e1(C=C)
        r2 = []
        r3, tr = e3(C=C)
    else:
        r1 = e1()
        r2 = e2()
        r3, tr = e3(C=E3_C)
    report(r1, r2, r3, tr)
    print(f"\nDone in {time.time() - t:.0f}s. See {OUT.resolve()}/results.md")
