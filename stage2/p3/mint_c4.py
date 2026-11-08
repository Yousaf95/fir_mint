"""C4: re-implementation of MINT's index tuner (Zhu et al., ICDE 2026, arXiv 2504.20018v3).

Implements, from the paper: plans (X, EK) with cost Eq. 4-6 in distance-computation units,
relevant-ek planning (Sec. III-C1; enumeration for |X_q| <= 3, Algorithm 1 DP otherwise),
numDist linear and recall logarithmic models per single-column index with multi-column indexes
estimated from the column average (Sec. III-C2), and Algorithm 2 beam search with di, se, b, im,
unused-index removal and plan caching (Sec. IV-B). Deviations and readings are listed in
stage2/p3/C4_DESIGN.md; the two that change numbers: exact full-table ranks for a query sample
(no data sample), and model fits on the full single-column indexes.

Search semantics assumed by the estimates: index x is searched with k = ek and
efSearch = max(ek, EF_FLOOR); the union of the results is re-ranked by the exact score.
"""
import itertools
import math
import time

import faiss
import numpy as np

EF_FLOOR = 100
EK_GRID = (100, 200, 400, 800, 1600, 3200)
QUANTS = (0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95, 0.97, 0.99, 1.0)


def subsets(q, min_size=1):
    return [x for m in range(min_size, len(q) + 1) for x in itertools.combinations(q, m)]


class Calibration:
    """One-time per table: model fits on the single-column indexes and the query-sample ranks."""

    def __init__(self, data, singles, train_q, k=10, n_fit=100, n_inst=100, di=2, seed=0):
        """data: list of (N, d_c) float32 arrays (normalised); singles: list of full HNSW indexes,
        one per column; train_q: list of (P, d_c) held-out query rows (training split)."""
        t0 = time.perf_counter()
        self.data, self.k, self.di = data, k, di
        self.C, self.N = len(data), data[0].shape[0]
        self.dim = [d.shape[1] for d in data]
        rng = np.random.default_rng(seed)
        P = train_q[0].shape[0]
        fit_rows = rng.choice(P, size=min(n_fit, P), replace=False)
        self.inst_rows = rng.choice(P, size=min(n_inst, P), replace=False)
        self.nd, self.rc, self.line_fit = [], [], []   # per column: (ek grid, ndis), (a, b)
        self.fit_points = []
        for c, ix in enumerate(singles):
            Q = np.ascontiguousarray(train_q[c][fit_rows])
            exact = data[c] @ Q.T                       # (N, n_fit)
            ex_top = np.argpartition(-exact, max(EK_GRID) - 1, axis=0)[:max(EK_GRID)]
            ex_sc = np.take_along_axis(exact, ex_top, 0)
            order = np.argsort(-ex_sc, axis=0)
            ex_top = np.take_along_axis(ex_top, order, 0)
            del exact
            pts = []
            for ek in EK_GRID:
                ix.hnsw.efSearch = max(ek, EF_FLOOR)
                faiss.cvar.hnsw_stats.reset()
                _, I = ix.search(Q, ek)
                ndis = faiss.cvar.hnsw_stats.ndis / len(Q)
                rec = np.mean([len(set(I[j]) & set(ex_top[:ek, j])) / ek for j in range(len(Q))])
                pts.append((ek, ndis, rec))
            e = np.array(pts)
            slope, inter = np.polyfit(e[:, 0], e[:, 1], 1)          # MINT's single line, kept for reporting
            b, a = np.polyfit(np.log(e[:, 0]), e[:, 2], 1)
            self.nd.append((e[:, 0].copy(), e[:, 1].copy())); self.rc.append((a, b)); self.fit_points.append(pts)
            self.line_fit.append(dict(intercept=float(inter), slope=float(slope),
                                      rel_err_at_grid=((inter + slope * e[:, 0]) / e[:, 1] - 1).round(4).tolist()))
        self.fit_s = time.perf_counter() - t0
        t1 = time.perf_counter()
        self.S = [np.ascontiguousarray(data[c] @ train_q[c][self.inst_rows].T) for c in range(self.C)]  # (N, P)
        self.ranks = {}                                 # q -> {x: (P, k) ranks}
        self.score_s = time.perf_counter() - t1
        self.rank_s = 0.0

    # ---- models (multi-column index = average over its columns)
    def ndist(self, x, ek):
        """Piecewise-linear through the measured points (linear extrapolation past the last one);
        multi-column index = average over its columns (MINT Sec. III-C2)."""
        ek = np.maximum(np.asarray(ek, float), EF_FLOOR)
        out = 0.0
        for c in x:
            g, n = self.nd[c]
            v = np.interp(ek, g, n)
            v = np.where(ek > g[-1], n[-1] + (ek - g[-1]) * (n[-1] - n[-2]) / (g[-1] - g[-2]), v)
            out = out + v
        return out / len(x)

    def ann_recall(self, x, ek):
        ek = np.maximum(ek, EF_FLOOR)
        r = np.mean([self.rc[c][0] for c in x]) + np.mean([self.rc[c][1] for c in x]) * np.log(ek)
        return np.clip(r, 0.0, 1.0)

    def idx_cost(self, x, ek):
        return np.where(np.asarray(ek) > 0, sum(self.dim[c] for c in x) * self.ndist(x, ek), 0.0)

    # ---- exact full-table ranks of each instance's ground truth under every useful index
    def prepare(self, q):
        if q in self.ranks:
            return self.ranks[q]
        t0 = time.perf_counter()
        k, P = self.k, len(self.inst_rows)
        F = sum(self.S[c] for c in q)                   # full score (sum; same ranking as mean)
        gt = np.argpartition(-F, k - 1, axis=0)[:k].T   # (P, k)
        out = {}
        for x in subsets(q, max(1, len(q) - self.di)):
            Px = F if x == q else sum(self.S[c] for c in x)
            R = np.empty((P, k), np.int64)
            for p in range(P):
                col = Px[:, p]
                v = col[gt[p]]
                above = np.sort(col[col > v.min()])     # only rows that can outrank some gt item
                R[p] = 1 + len(above) - np.searchsorted(above, v, side="right")
            out[x] = R
        self.ranks[q] = out
        self.rank_s += time.perf_counter() - t0
        return out

    @property
    def calib_s(self):
        return self.fit_s + self.score_s + self.rank_s


class Planner:
    """Best plan (EK) for query type q over the useful indexes X_q (Sec. III)."""

    def __init__(self, cal, theta, k_prime=5, n_dp_samples=4, seed=0):
        self.cal, self.theta, self.kp, self.ns = cal, theta, k_prime, n_dp_samples
        self.rng = np.random.default_rng(seed)
        self.cache, self.calls, self.hits = {}, 0, 0

    def useful(self, q, X):
        return tuple(sorted(x for x in X if set(x) <= set(q) and len(x) >= len(q) - self.cal.di))

    def _evaluate(self, q, Xq, E):
        """E: (M, |Xq|) candidate EKs. Returns cost (M,), expected recall (M,)."""
        cal, R = self.cal, self.cal.prepare(q)
        miss = np.ones((E.shape[0],) + R[Xq[0]].shape)
        cost = np.zeros(E.shape[0])
        for i, x in enumerate(Xq):
            e = E[:, i]
            hit = R[x][None] <= e[:, None, None]
            miss *= 1.0 - cal.ann_recall(x, e)[:, None, None] * hit
            cost += cal.idx_cost(x, e)
        cost += sum(cal.dim[c] for c in q) * E.sum(1)   # re-rank cost, Eq. 6
        return cost, (1.0 - miss).mean(axis=(1, 2))

    def _dp_candidates(self, q, Xq):
        """Algorithm 1 on k' sampled ground-truth items of several instances."""
        cal, R = self.cal, self.cal.prepare(q)
        P, k = R[Xq[0]].shape
        need = math.ceil(self.kp * self.theta)
        full = (1 << self.kp) - 1
        cands = []
        for _ in range(self.ns):
            p = int(self.rng.integers(P)); items = self.rng.choice(k, size=self.kp, replace=False)
            e = [R[x][p, items] for x in Xq]            # relevant ek per index for the k' items
            def cover_cost(i, mask):
                if mask == 0:
                    return 0.0, 0
                ek = int(max(e[i][j] for j in range(self.kp) if mask >> j & 1))
                return float(cal.idx_cost(Xq[i], ek)), ek
            DP = {m: cover_cost(0, m)[0] for m in range(full + 1)}
            EK = {m: (cover_cost(0, m)[1],) for m in range(full + 1)}
            for i in range(1, len(Xq)):
                nDP, nEK = {}, {}
                for m in range(full + 1):
                    best, arg = math.inf, None
                    sub = m
                    while True:                          # all cvr subset of cover
                        c, ek = cover_cost(i, sub)
                        v = DP[m & ~sub] + c
                        if v < best:
                            best, arg = v, EK[m & ~sub] + (ek,)
                        if sub == 0:
                            break
                        sub = (sub - 1) & m
                    nDP[m], nEK[m] = best, arg
                DP, EK = nDP, nEK
            ok = [m for m in range(full + 1) if bin(m).count("1") >= need]
            cands.append(EK[min(ok, key=lambda m: DP[m])])
        return np.array(cands, float)

    def plan(self, q, X):
        Xq = self.useful(q, X)
        key = (q, Xq)
        if key in self.cache:
            self.hits += 1
            return self.cache[key]
        self.calls += 1
        if not Xq:
            res = (math.inf, 0.0, {})
        else:
            R = self.cal.prepare(q)
            if len(Xq) <= 3:
                grids = [np.unique(np.concatenate(([0], np.quantile(R[x], QUANTS, method="higher")))) for x in Xq]
                E = np.array(list(itertools.product(*grids)), float)
            else:
                E = self._dp_candidates(q, Xq)
                E = np.vstack([E, E.max(0, keepdims=True)])
                for y in Xq:                             # best plans without one index: adding an
                    sub = tuple(z for z in Xq if z != y)  # index can never make the plan worse
                    _, _, ek = self.plan(q, sub)
                    E = np.vstack([E, [[ek.get(x, 0) for x in Xq]]])
            E = E[E.sum(1) > 0]
            cost, rec = self._evaluate(q, Xq, E)
            ok = rec >= self.theta
            i = int(np.argmin(np.where(ok, cost, np.inf))) if ok.any() else int(np.argmax(rec))
            res = (float(cost[i]), float(rec[i]), {x: int(E[i, j]) for j, x in enumerate(Xq) if E[i, j] > 0})
        self.cache[key] = res
        return res


class Tuner:
    """Algorithm 2 (beam search). Storage is the sum of index widths over multi-column indexes
    (single-column indexes fixed, brief 6.5) or, in MINT's own setting, the number of indexes."""

    def __init__(self, cal, theta, budget, beam=5, di=2, se=2, im=0.05, fixed_singles=True,
                 storage_mode="units", seed=0):
        self.cal, self.theta, self.budget = cal, theta, budget
        self.b, self.di, self.se, self.im = beam, di, se, im
        self.fixed_singles, self.storage_mode = fixed_singles, storage_mode
        self.singles = frozenset((c,) for c in range(cal.C)) if fixed_singles else frozenset()
        self.planner = Planner(cal, theta, seed=seed)
        self.log = []

    def storage(self, X):
        if self.storage_mode == "count":
            return len(X)
        return sum(len(x) for x in X if len(x) > 1)

    def cand(self, q):
        lo = max(1 if not self.fixed_singles else 2, len(q) - self.di)
        return [x for x in subsets(q, lo)]

    def evaluate(self, W, X):
        viol = cost = 0.0
        used = set()
        for q, w in W.items():
            c, r, ek = self.planner.plan(q, X)
            if r < self.theta:
                viol += w
            cost += w * (c if math.isfinite(c) else 1e18)
            used |= set(ek)
        return round(viol, 12), cost, used

    def prune(self, W, X):
        _, _, used = self.evaluate(W, X)
        return frozenset(x for x in X if x in used or x in self.singles)

    def tune(self, W, start=None):
        """W: {query type: weight}. start: current configuration (warm start)."""
        t0 = time.perf_counter(); c0 = self.planner.calls
        W = {q: w for q, w in W.items() if w > 0}
        cands = sorted({x for q in W for x in self.cand(q)})
        seeds = {self.singles}
        for q in W:
            cq = self.cand(q)
            for m in range(1, self.se + 1):
                seeds |= {self.singles | frozenset(s) for s in itertools.combinations(cq, m)}
        if start is not None:
            seeds.add(frozenset(start) | self.singles)
        def key(X):
            v, c, _ = self.evaluate(W, X)
            return (v, c)
        scored = sorted(((key(X), X) for X in seeds if self.storage(X) <= self.budget), key=lambda t: t[0])
        best_ever = min(scored, key=lambda t: t[0])
        beam = scored[:self.b]
        it = 0
        while True:
            it += 1
            nxt = {}
            for _, X in beam:
                for x in cands:
                    if x in X:
                        continue
                    Y = self.prune(W, X | {x})
                    if self.storage(Y) <= self.budget and Y not in nxt:
                        nxt[Y] = key(Y)
            if not nxt:
                break
            new = sorted(((v, X) for X, v in nxt.items()), key=lambda t: t[0])[:self.b]
            old_best, new_best = beam[0][0], new[0][0]
            if new_best < best_ever[0]:
                best_ever = new[0]
            improved = new_best[0] < old_best[0] or (new_best[0] == old_best[0] and
                                                     new_best[1] < old_best[1] * (1 - self.im))
            beam = new
            if not improved:
                break
        X, (v, c) = best_ever[1], best_ever[0]
        res = dict(config=sorted(X), viol=v, cost=c, iterations=it, tune_s=time.perf_counter() - t0,
                   planner_calls=self.planner.calls - c0, n_seeds=len(seeds), n_cands=len(cands))
        self.log.append(res)
        return res
