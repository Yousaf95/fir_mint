"""Pilot P3: tuner cost and faithfulness of C4 (stage2/p3/P3_PROTOCOL.md, fixed before this run).

Usage (repository root, exclusive node):
  python stage2/p3/p3_run.py --data embeddings/laion_1m_4col --out results/p3
"""
import argparse, hashlib, importlib.util, json, os, platform, resource, subprocess, sys, time
from pathlib import Path

import faiss
import numpy as np
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
import mint_c4 as m4

BUILD_THREADS = int(os.environ.get("FIR_BUILD_THREADS", "28"))
HNSW_M, EF_CONS, K, THETA, BUDGET = 32, 128, 10, 0.90, 8


def normalize(x):
    return x / np.maximum(np.linalg.norm(x, axis=-1, keepdims=True), 1e-12)


def load_frozen(tmp):
    want = {l.split()[1]: l.split()[0] for l in open(ROOT / "code_frozen" / "SHA256SUMS") if l.strip()}
    f = ROOT / "code_frozen" / "fir_mint_v4.py"
    assert want["fir_mint_v4.py"] == hashlib.sha256(f.read_bytes()).hexdigest()
    cwd = os.getcwd(); os.chdir(tmp)
    spec = importlib.util.spec_from_file_location("fm", f)
    fm = importlib.util.module_from_spec(spec); spec.loader.exec_module(fm); os.chdir(cwd)
    return fm


def build(vecs):
    ix = faiss.IndexHNSWFlat(vecs.shape[1], HNSW_M, faiss.METRIC_INNER_PRODUCT)
    ix.hnsw.efConstruction = EF_CONS
    faiss.omp_set_num_threads(BUILD_THREADS)
    t0, c0 = time.perf_counter(), time.process_time()
    ix.add(np.ascontiguousarray(vecs, dtype=np.float32))
    wall, cpu = time.perf_counter() - t0, time.process_time() - c0
    faiss.omp_set_num_threads(1)
    return ix, wall, cpu


def mint_workload(C, n, rng):
    """MINT Sec. V-A: each column selected independently with p = 0.5; distinct non-empty queries;
    weights i.i.d. Uniform(0,1), normalised."""
    qs = []
    while len(qs) < n:
        q = tuple(c for c in range(C) if rng.random() < 0.5)
        if q and q not in qs:
            qs.append(q)
    w = rng.uniform(0, 1, n); w /= w.sum()
    return {q: float(x) for q, x in zip(qs, w)}


def measure(data, Q, idx, plans, test, gt, k=K, rounds=3):
    """Execute C4 plans: each index searched with k = ek, efSearch = max(ek, 100); union re-ranked
    by the exact score; warm-up round + `rounds` timed rounds, median of round means."""
    T = {t: i for i, t in enumerate(gt["types"])}
    def run(q, r):
        ek = plans[q]
        t0 = time.perf_counter()
        cand = []
        for x, e in ek.items():
            ix = idx[x]; ix.hnsw.efSearch = max(e, m4.EF_FLOOR)
            v = normalize(np.concatenate([Q[c][r] for c in x]))[None].astype(np.float32)
            _, I = ix.search(v, e); cand.append(I[0][I[0] >= 0])
        cand = np.unique(np.concatenate(cand))
        s = sum(data[c][cand] @ Q[c][r] for c in q)
        res = cand[np.argsort(-s)[:k]]
        return res, (time.perf_counter() - t0) * 1000
    means = []
    for rnd in range(rounds + 1):
        ts = [run(q, r)[1] for q, r in test]
        if rnd: means.append(np.mean(ts))
    rec = {}
    for q, r in test:
        res, _ = run(q, r)
        ti = T[q]; b = float(gt["boundary"][ti, r]); tol = max(1e-6, abs(b) * 1e-6)
        rel = gt["ids"][ti, r][gt["scores"][ti, r] >= b - tol]
        rec.setdefault(q, []).append(min(1.0, len(set(res.tolist()) & set(rel.tolist())) / min(k, len(rel))))
    allr = np.concatenate([v for v in rec.values()])
    return dict(latency_ms=float(np.median(means)), per_type_recall={"-".join(map(str, q)): float(np.mean(v)) for q, v in rec.items()},
                min_type_recall=float(min(np.mean(v) for v in rec.values())), query_violation_rate=float((allr < THETA).mean()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True); ap.add_argument("--out", default="results/p3")
    ap.add_argument("--seeds", type=int, nargs="*", default=[0, 1, 2, 3, 4])
    ap.add_argument("--mint_sizes", type=int, nargs="*", default=[10, 12, 14])
    ap.add_argument("--timing_only", action="store_true",
                    help="calibration, warm/cold and repeats only (tuner cost for P2a on other tables)")
    a = ap.parse_args()
    folder = (ROOT / a.data).resolve(); out = (ROOT / a.out / folder.name).resolve(); out.mkdir(parents=True, exist_ok=True)
    fm = load_frozen(out)
    t_start = time.time()
    cols = json.load(open(folder / "meta.json"))["columns"]
    data = [np.ascontiguousarray(np.load(folder / f"data_{c}.npy"), dtype=np.float32) for c in cols]
    Qall = [np.ascontiguousarray(np.load(folder / f"query_{c}.npy"), dtype=np.float32) for c in cols]
    C, nq = len(cols), Qall[0].shape[0]
    train_rows, test_rows = np.arange(nq // 2), np.arange(nq // 2, nq)    # disjoint pools
    gt = dict(np.load(folder / "gt.npz")) if not a.timing_only else None
    if gt is not None: gt["types"] = [tuple(int(c) for c in t if c >= 0) for t in gt["types"]]
    R = dict(columns=cols, rows=int(data[0].shape[0]), train_rows=[0, nq // 2], test_rows=[nq // 2, nq])
    log = lambda *x: print(*x, flush=True)

    # ---- single-column indexes (build time, reported separately; R1)
    singles, R["single_builds"] = [], []
    for c in range(C):
        ix, w, cpu = build(data[c]); singles.append(ix)
        R["single_builds"].append(dict(column=cols[c], wall_s=w, cpu_s=cpu)); log("built", cols[c], f"{w:.0f}s")

    # ---- calibration (draft setting k = 10), all 14 query types prepared
    types = [q for mm in (1, 2, 3) for q in __import__("itertools").combinations(range(C), mm)]   # draft: sizes 1-3
    cal = m4.Calibration(data, singles, [q[train_rows] for q in Qall], k=K)
    for q in types: cal.prepare(q)
    R["calibration"] = dict(fit_s=cal.fit_s, score_s=cal.score_s, rank_s=cal.rank_s, total_s=cal.calib_s,
                            fit_points=cal.fit_points, single_line_fit=cal.line_fit, ann_recall=cal.rc)
    log("calibration", {k: round(v, 1) for k, v in R["calibration"].items() if k.endswith("_s")})

    # ---- warm vs cold, draft workloads (abrupt axis-U drift), seeds
    R["warm_cold"] = []
    for seed in a.seeds:
        rng = np.random.default_rng(1000 + seed)
        p0 = fm.zipf_dist(C, rng, single_mass=0.85); p1 = fm.zipf_dist(C, rng, single_mass=0.35)
        T = m4.Tuner(cal, THETA, BUDGET, beam=5)
        r0 = T.tune(p0)
        rw = T.tune(p1, start=r0["config"])
        rc = m4.Tuner(cal, THETA, BUDGET, beam=5).tune(p1)
        row = dict(seed=seed, stable=r0, warm=rw, cold=rc,
                   cut_tuning_only=1 - rw["tune_s"] / rc["tune_s"],
                   cut_incl_calibration=1 - rw["tune_s"] / (rc["tune_s"] + cal.calib_s),
                   warm_cost_vs_cold=rw["cost"] / rc["cost"] - 1, p0={"-".join(map(str, q)): w for q, w in p0.items()},
                   p1={"-".join(map(str, q)): w for q, w in p1.items()})
        R["warm_cold"].append(row)
        log(f"seed {seed}: cold {rc['tune_s']:.2f}s warm {rw['tune_s']:.2f}s cut {row['cut_tuning_only']:.1%} "
            f"cost warm/cold-1 {row['warm_cost_vs_cold']:+.3%} cfg warm {rw['config']} cold {rc['config']}")

    # ---- timing repetitions (seed 0) and beam sweep
    rng = np.random.default_rng(1000); p0 = fm.zipf_dist(C, rng, single_mass=0.85); p1 = fm.zipf_dist(C, rng, single_mass=0.35)
    R["repeat_seed0"] = [m4.Tuner(cal, THETA, BUDGET, beam=5).tune(p1)["tune_s"] for _ in range(5)]
    R["beam_sweep"] = []
    for b in (3, 5, 10):
        r = m4.Tuner(cal, THETA, BUDGET, beam=b).tune(p1)
        R["beam_sweep"].append(dict(beam=b, tune_s=r["tune_s"], cost=r["cost"], config=r["config"], calls=r["planner_calls"]))
    log("repeat", np.round(R["repeat_seed0"], 2), "beam", [(x["beam"], round(x["tune_s"], 2), round(x["cost"])) for x in R["beam_sweep"]])

    if a.timing_only:
        cuts = [x["cut_tuning_only"] for x in R["warm_cold"]]
        R["warm_start_cut_median"] = float(np.median(cuts))
        commit = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
        R["provenance"] = dict(commit=commit, host=platform.node(), pbs_job=os.environ.get("PBS_JOBID"), mode="timing_only",
                               build_threads=BUILD_THREADS, label="measured", elapsed_s=time.time() - t_start)
        json.dump(R, open(out / "p3_timing.json", "w"), indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o))
        log("timing only done; median warm cut", R["warm_start_cut_median"])
        return

    # ---- measured Static configuration (seed 0, stable workload): window ratio + estimate check
    T = m4.Tuner(cal, THETA, BUDGET, beam=5); r0 = T.tune(p0)
    idx = {(c,): singles[c] for c in range(C)}; R["multi_builds"] = []
    for x in r0["config"]:
        if len(x) > 1:
            ix, w, cpu = build(normalize(np.hstack([data[c] for c in x]))); idx[x] = ix
            R["multi_builds"].append(dict(index=list(x), wall_s=w, cpu_s=cpu)); log("built", x, f"{w:.0f}s")
    plans = {q: T.planner.plan(q, frozenset(r0["config"]))[2] for q in types}
    keys = list(p0); trng = np.random.default_rng(7)
    test = [(keys[i], int(trng.choice(test_rows))) for i in trng.choice(len(keys), 600, p=[p0[q] for q in keys])]
    with threadpool_limits(limits=1):                 # single-threaded search and re-rank
        meas = measure(data, Qall, idx, plans, test, gt)
    est_rec = {"-".join(map(str, q)): T.planner.plan(q, frozenset(r0["config"]))[1] for q in types}
    window_s = 10_000 * meas["latency_ms"] / 1000
    R["static_measured"] = dict(config=r0["config"], **meas, estimated_recall=est_rec, window_s_at_Qw_10000=window_s,
                                tuner_to_window_cold=(R["warm_cold"][0]["cold"]["tune_s"] + cal.calib_s) / window_s,
                                tuner_to_window_warm=R["warm_cold"][0]["warm"]["tune_s"] / window_s)
    log("static measured", {k: v for k, v in R["static_measured"].items() if k not in ("per_type_recall", "estimated_recall")})

    # ---- faithfulness: MINT's workload construction, recall@100, count storage = C indexes
    cal100 = cal.with_k(100)
    all_q = [q for mm in range(1, C + 1) for q in __import__("itertools").combinations(range(C), mm)]
    t0 = time.perf_counter()
    for q in all_q: cal100.prepare(q)
    R["faithful_calibration_s"] = dict(rank_s=time.perf_counter() - t0, shared_fit_s=cal.fit_s, shared_score_s=cal.score_s)
    R["faithful"] = []
    for n in a.mint_sizes:
        for seed in a.seeds:
            W = mint_workload(C, n, np.random.default_rng(2000 + 100 * n + seed))
            r = m4.Tuner(cal100, THETA, budget=C, beam=5, fixed_singles=False, storage_mode="count").tune(W)
            R["faithful"].append(dict(n_queries=n, seed=seed, tune_s=r["tune_s"], config=r["config"], viol=r["viol"],
                                      calls=r["planner_calls"], iterations=r["iterations"]))
            log(f"MINT workload n={n} seed={seed}: tune {r['tune_s']:.1f}s viol {r['viol']} cfg {r['config']}")
    med = {n: float(np.median([x["tune_s"] for x in R["faithful"] if x["n_queries"] == n])) for n in a.mint_sizes}
    cuts = [x["cut_tuning_only"] for x in R["warm_cold"]]
    R["pass"] = dict(
        faithfulness=dict(medians_s=med, band_s=[85 / 3, 185 * 3], result="PASS" if all(85 / 3 <= v <= 185 * 3 for v in med.values()) else "FAIL"),
        warm_start=dict(median_cut_tuning_only=float(np.median(cuts)), per_seed=cuts, threshold=0.30,
                        result="PASS" if np.median(cuts) >= 0.30 else "FAIL"))
    commit = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    R["provenance"] = dict(commit=commit, host=platform.node(), pbs_job=os.environ.get("PBS_JOBID"), build_threads=BUILD_THREADS,
                           search_threads=1, blas_threads=os.environ.get("OPENBLAS_NUM_THREADS"), label="measured",
                           elapsed_s=time.time() - t_start, peak_rss_gb=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 ** 2)
    json.dump(R, open(out / "p3.json", "w"), indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o))
    log(json.dumps(R["pass"], indent=1))


if __name__ == "__main__":
    main()
