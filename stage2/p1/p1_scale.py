"""Pilot P1 (brief Part 6.8): does re-tuning still pay at 1M rows?

Runs the draft's E1 procedure (code_frozen/fir_mint_v4.py, function e1) unchanged on a larger
table: per seed, Static is tuned on a stable window, FIR-MINT (warm start) and Full re-tune on two
drifted windows (one abrupt axis-U drift), each configuration is built and timed on 600 held-out
queries (warm-up round + 3 interleaved rounds, median of round means).

Changes against v1.0, all outside the tuner:
  * recall_of uses exact ground truth precomputed on GPU (prep_laion.py) instead of a numpy scan of
    all rows per query; same tie-aware definition. Checked against the original inside the run.
  * make_query consumes the RNG exactly as v1.0 and also remembers the query row.
Added measurements (brief P1): build time and memory per index, flat-scan latency per query type,
per-query recall (multiples of 1/k), per-type latency, peak RSS, paired statistics with a sign
test and a bootstrap interval (10,000 resamples, marked indicative with 5 seeds).

Usage (repository root): FIR_BUILD_THREADS=28 python stage2/p1/p1_scale.py --data embeddings/laion_1m_4col
"""
import argparse, hashlib, importlib.util, json, os, platform, resource, subprocess, sys, time
from math import comb
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
# commit of the code this process runs, read at start (later commits must not leak in)
START_COMMIT = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
FROZEN = ROOT / "code_frozen" / "fir_mint_v4.py"


def load_frozen(workdir):
    want = {l.split()[1].lstrip("*"): l.split()[0] for l in open(ROOT / "code_frozen" / "SHA256SUMS") if l.strip()}
    got = hashlib.sha256(FROZEN.read_bytes()).hexdigest()
    assert want.get("fir_mint_v4.py") == got, "frozen fir_mint_v4.py does not match SHA256SUMS"
    cwd = os.getcwd(); os.chdir(workdir)                     # the module creates its OUT folder on import
    spec = importlib.util.spec_from_file_location("fm", FROZEN)
    fm = importlib.util.module_from_spec(spec); spec.loader.exec_module(fm)
    os.chdir(cwd)
    return fm, got


class QV(dict):
    row = -1


def install_gt(fm, folder):
    g = np.load(Path(folder) / "gt.npz")
    types = [tuple(int(c) for c in t if c >= 0) for t in g["types"]]
    T = {t: i for i, t in enumerate(types)}
    ids, sc, bnd, nrel = g["ids"], g["scores"], g["boundary"], g["n_relevant"]
    keep = ids.shape[2]
    orig_recall, orig_make = fm.recall_of, fm.make_query
    stats = {"fallback": 0}

    def make_query(data, q, rng):
        r = int(rng.integers(0, len(fm.REAL_Q[0])))          # identical RNG use to v1.0
        v = QV({c: fm.REAL_Q[c][r] for c in q}); v.row = r
        return v

    def recall_of(store, q, plan, qv):
        ti, r = T[q], qv.row
        if nrel[ti, r] > keep:                               # more ties than stored: use the original
            stats["fallback"] += 1
            return orig_recall(store, q, plan, qv)
        got, _ = fm.run_plan(store, plan, q, qv)
        b = float(bnd[ti, r]); tol = max(1e-6, abs(b) * 1e-6)
        relevant = ids[ti, r][sc[ti, r] >= b - tol]
        return min(1.0, len(set(got.tolist()) & set(relevant.tolist())) / min(fm.TOP_K, len(relevant)))

    fm.make_query, fm.recall_of = make_query, recall_of
    return orig_recall, stats


def validate(fm, orig_recall, store, est, rng, n=24):
    """Patched recall must equal the original brute-force recall on real plans."""
    out = []
    types = fm.types_for(len(fm.REAL))
    full = frozenset(t for t in types if len(t) > 1)
    for _ in range(n):
        q = types[int(rng.integers(len(types)))]
        qv = fm.make_query(fm.REAL, q, rng)
        plan = est.best_plan(q, full if rng.random() < 0.5 else frozenset())[0]
        a, b = orig_recall(store, q, plan, qv), fm.recall_of(store, q, plan, qv)
        out.append(dict(type=list(q), row=qv.row, plan=plan[0], original=a, ground_truth=b))
    bad = [o for o in out if abs(o["original"] - o["ground_truth"]) > 1e-9]
    assert not bad, f"ground-truth recall differs from v1.0 recall_of: {bad}"
    return out


def index_memory(ix):
    raw = ix.ntotal * ix.d * 4
    graph = 0
    if hasattr(ix, "hnsw"):
        h = ix.hnsw
        graph = 4 * (h.neighbors.size() + h.levels.size()) + 8 * h.offsets.size()
    return raw, graph


def flat_scan_ms(fm, store, q, rng, n=30):
    ts = []
    for _ in range(n):
        qv = fm.make_query(fm.REAL, q, rng)
        t0 = time.perf_counter(); fm.topk(fm.joint(store.data, q, qv), fm.TOP_K); ts.append(time.perf_counter() - t0)
    return float(np.median(ts)) * 1000


def paired_summary(a, b, rng, B=10_000):
    d = (np.asarray(a) / np.asarray(b) - 1) * 100
    boot = rng.choice(d, size=(B, len(d)), replace=True).mean(1)
    lo, hi = np.percentile(boot, [2.5, 97.5])
    neg = int((d < 0).sum()); n = len(d); k = min(neg, n - neg)
    p_sign = min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n)
    return dict(per_seed_pct=d.round(3).tolist(), mean_pct=float(d.mean()), boot_ci=[float(lo), float(hi)],
                n_seeds=n, seeds_lower=neg, sign_test_p=p_sign, interval_label="indicative (5 seeds)")


def run(fm, folder, out):
    C = fm.load_real(folder)
    orig_recall, gt_stats = install_gt(fm, folder)
    t_start = time.time()
    rows, per_query, per_type_lat, checks = [], [], [], None
    for seed in fm.SEEDS:                                   # --- verbatim e1() logic, plus records
        rng = np.random.default_rng(seed)
        data = fm.gen_data(C, rng)
        store = fm.get_store(data)
        t0 = time.time(); est = fm.Estimator(store, rng); calib_s = time.time() - t0
        if checks is None:
            checks = validate(fm, orig_recall, store, est, np.random.default_rng(1234))
        p0 = fm.zipf_dist(C, rng, single_mass=0.85)
        p1 = fm.zipf_dist(C, rng, single_mass=0.35)
        static, _, _, _ = fm.full_retune(est, fm.sample_window(p0, rng))
        for i in static: store.get(i)
        obs = {k: (a + b) / 2 for (k, a), b in zip(fm.sample_window(p1, rng).items(), fm.sample_window(p1, rng).values())}
        fir, _, fir_calls, fir_t = fm.fir_retune(est, obs, static)
        full, _, full_calls, full_t = fm.full_retune(est, obs)

        keys = list(p1)
        test = [keys[i] for i in rng.choice(len(keys), 600, p=[p1[k] for k in keys])]
        qvs = [fm.make_query(data, q, rng) for q in test]
        pols = [("Static", static, 0, 0.0), ("FIR-MINT", fir, fir_calls, fir_t), ("Full re-tune", full, full_calls, full_t)]
        plans, build = {}, {}
        for name, cfg, _, _ in pols:
            new = [i for i in cfg if i not in static]
            for i in cfg: store.get(i)
            build[name] = (len(new), sum(store.build_s[i] for i in new))
            plans[name] = [est.best_plan(q, cfg)[0] for q in test]
        lat = {name: [] for name, *_ in pols}
        for rnd in range(4):                                # round 0 = warm-up
            order = pols[rnd % 3:] + pols[:rnd % 3]
            for name, *_ in order:
                ts = [fm.run_plan(store, pl, q, qv)[1] for q, qv, pl in zip(test, qvs, plans[name])]
                if rnd > 0:
                    lat[name].append(ts)
        for name, cfg, calls, tt in pols:
            rec = {}
            for j, (q, qv, pl) in enumerate(zip(test, qvs, plans[name])):
                r = fm.recall_of(store, q, pl, qv)
                rec.setdefault(q, []).append(r)
                per_query.append(dict(seed=seed, strategy=name, query_type="-".join(map(str, q)), row=qv.row,
                                      plan=pl[0], pool=pl[2], recall=r, latency_ms=float(np.median([L[j] for L in lat[name]]))))
            per_type = {q: np.mean(v) for q, v in rec.items()}
            viol = sum(p1[q] for q, r in per_type.items() if r < fm.RECALL_TARGET)
            allr = np.concatenate([v for v in rec.values()])
            means = [np.mean(t) for t in lat[name]]
            allt = np.concatenate(lat[name])
            rows.append(dict(seed=seed, policy=name, latency_ms=float(np.median(means)),
                             p95_ms=float(np.percentile(allt, 95)), p99_ms=float(np.percentile(allt, 99)),
                             min_recall=float(min(per_type.values())), viol_mass=float(viol),
                             recall_mean=float(allr.mean()), recall_p5=float(np.percentile(allr, 5)),
                             query_violation_rate=float((allr < fm.RECALL_TARGET).mean()),
                             whatif=calls, tune_s=tt, calib_s=calib_s, new_indexes=build[name][0], build_s=build[name][1],
                             storage=fm.storage(cfg), config=[list(i) for i in sorted(cfg)]))
            r_ = rows[-1]
            print(f"[P1 seed {seed}] {name:12s} lat={r_['latency_ms']:.3f}ms p95={r_['p95_ms']:.3f} "
                  f"typeMinRec={r_['min_recall']:.3f} qViol={r_['query_violation_rate']:.3f} whatif={calls} "
                  f"new={build[name][0]} build={build[name][1]:.0f}s cfg={sorted(cfg)}", flush=True)
            for q in set(test):
                ts = [np.median([L[j] for L in lat[name]]) for j, t in enumerate(test) if t == q]
                per_type_lat.append(dict(seed=seed, strategy=name, query_type="-".join(map(str, q)),
                                         n=len(ts), median_ms=float(np.median(ts)), mass=p1[q]))
        json.dump(dict(rows=rows), open(out / "p1_partial.json", "w"))   # checkpoint per seed

    store = fm.get_store(None)
    idx = []
    for key, ix in sorted(store.idx.items()):
        raw, graph = index_memory(ix)
        idx.append(dict(key=list(key), dim=ix.d, kind=type(ix).__name__, build_s=store.build_s[key],
                        raw_bytes=raw, graph_bytes=graph))
    frng = np.random.default_rng(99)
    flat = {"-".join(map(str, q)): flat_scan_ms(fm, store, q, frng) for q in fm.types_for(C)}

    srng = np.random.default_rng(2026)
    by = {(r["seed"], r["policy"]): r for r in rows}
    seeds = sorted({r["seed"] for r in rows})
    summ = {f"{a} vs {b}": paired_summary([by[(s, a)]["latency_ms"] for s in seeds], [by[(s, b)]["latency_ms"] for s in seeds], srng)
            for a, b in (("FIR-MINT", "Static"), ("Full re-tune", "Static"), ("FIR-MINT", "Full re-tune"))}
    s = summ["FIR-MINT vs Static"]
    passed = s["seeds_lower"] == s["n_seeds"] and s["boot_ci"][1] < 0
    return dict(rows=rows, summary=summ, pass_condition=dict(
                    text="paired per-seed differences all in the same direction (sign test) and a bootstrap "
                         "interval, marked indicative with 5 seeds, that excludes zero (brief P1, confirmed 2026-11-08)",
                    direction_all_lower=s["seeds_lower"] == s["n_seeds"], ci_excludes_zero=s["boot_ci"][1] < 0,
                    result="PASS" if passed else "FAIL"),
                indexes=idx, flat_scan_ms=flat, per_type_latency=per_type_lat, recall_validation=checks,
                gt_fallbacks=gt_stats["fallback"], elapsed_s=time.time() - t_start,
                peak_rss_gb=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 ** 2), per_query


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True); ap.add_argument("--out", default="results/p1")
    ap.add_argument("--seeds", type=int, nargs="*", help="override seeds (smoke tests only)")
    a = ap.parse_args()
    folder = Path(a.data) if Path(a.data).is_absolute() else (ROOT / a.data).resolve()
    base = Path(a.out) if Path(a.out).is_absolute() else ROOT / a.out
    out = (base / folder.name).resolve(); out.mkdir(parents=True, exist_ok=True)
    fm, sha = load_frozen(out)
    fm.OUT = out
    if a.seeds:
        fm.SEEDS = a.seeds
    res, per_query = run(fm, folder, out)
    commit = START_COMMIT
    res["provenance"] = dict(commit=commit, frozen_sha256=sha, host=platform.node(), python=sys.version.split()[0],
                             build_threads=fm.BUILD_THREADS, search_threads=1, pbs_job=os.environ.get("PBS_JOBID"),
                             seeds=fm.SEEDS, label="measured")
    json.dump(res, open(out / "p1.json", "w"), indent=1)
    with open(out / "recall_by_query.csv", "w") as f:
        f.write("seed,strategy,query_type,row,plan,pool,recall,latency_ms\n")
        for r in per_query:
            f.write(f"{r['seed']},{r['strategy']},{r['query_type']},{r['row']},{r['plan']},{r['pool']},{r['recall']},{r['latency_ms']:.5f}\n")
    with open(out / "summary.csv", "w") as f:
        f.write("exp,dataset,scenario,strategy,metric,label,mean,ci_low,ci_high,n_seeds\n")
        for k, v in res["summary"].items():
            f.write(f"P1,{folder.name},abrupt,{k},latency_change_pct,measured,{v['mean_pct']:.4f},"
                    f"{v['boot_ci'][0]:.4f},{v['boot_ci'][1]:.4f},{v['n_seeds']}\n")
    print(json.dumps({k: v for k, v in res.items() if k in ("summary", "pass_condition", "flat_scan_ms", "peak_rss_gb", "elapsed_s")}, indent=1))


if __name__ == "__main__":
    main()
