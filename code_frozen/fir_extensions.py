"""
FIR-MINT extensions (E6): fast-path drift detection and cost-aware switching.

Imports the frozen fir_mint_v4.py and fir_baselines.py WITHOUT modifying them. Uses the same
estimators, scenarios, seeds and window samples as fir_baselines.py (E4), so the FIR+detector
rows reproduce the E4 values exactly (built-in consistency check).

New mechanisms
  Fast path (FIR+fast): besides the sustained-drift rule (2 windows above mean + 3 sigma), re-tune
    immediately after ONE window whose divergence exceeds mean + K_FAST sigma of the bootstrap
    distribution (default K_FAST = 10), i.e. far beyond sampling noise. Targets detection delay.
  Ski-rental switching (FIR+SR): when the detector fires, FIR proposes X' but does not switch yet.
    Each window it accumulates the excess query time of staying with X,
        R += Q_w * (J(X; h_t) - J(X'; h_t)),
    and switches once R reaches the build time of the new indexes in X' \\ X (the classic
    deterministic ski-rental rule, 2-competitive for the switch decision; no horizon parameter).
    The proposal is dropped after 2 windows without positive excess cost, and replaced if the
    detector fires again. Recall comes first: if X violates the recall target on the window
    and X' does not, switch immediately. Q_w = queries per window in production.

Evaluation
  Query-cost regret vs hindsight re-tune (as E4), false re-tunes, delay, builds.
  Total time = query time (Q_w * J summed over windows) + index build time, for Q_w in
  {1e3, 1e4, 1e5}. Build time per index is modeled from the measured FAISS build times of the
  calibration store, by index width.

Usage (from the folder containing frozen fir_mint_v4.py and fir_baselines.py, or with PYTHONPATH):
  python fir_extensions.py                       # synthetic
  python fir_extensions.py --data <vectors>      # real data
  python fir_extensions.py --seeds 0 --out smoke  # quick test
"""
import argparse, json, time
from pathlib import Path
import numpy as np
import fir_mint_v4 as F
import fir_baselines as B

K_FAST = 10.0
HORIZON = 10
QW_LEVELS = (1_000, 10_000, 100_000)
SCENARIOS = B.SCENARIOS


class FastDetector(B.ParamDetector):
    """Frozen detector logic plus a single-window fast path for very large divergence."""

    def __init__(self, ref, rng, win, k_sigma=3.0, k_fast=K_FAST):
        self.k_fast = k_fast
        super().__init__(ref, rng, win, k_sigma)

    def reset(self, ref):
        self.ref, self.hits, self.cool, self.buf = ref, 0, self.cooldown, []
        sm = B.smooth(ref)
        s = [F.kl(F.sample_window(sm, self.rng, n=self.win), F.sample_window(sm, self.rng, n=self.win))
             for _ in range(300)]
        self.thr = float(np.mean(s) + self.k * np.std(s))
        self.thr_fast = float(np.mean(s) + self.k_fast * np.std(s))

    def observe(self, w):
        if self.cool > 0:
            self.cool -= 1
            return None
        d = F.kl(w, self.ref)
        if d > self.thr_fast:
            self.hits, self.buf = 0, []
            return w
        if d > self.thr:
            self.hits += 1; self.buf.append(w)
        else:
            self.hits, self.buf = 0, []
        return B.pooled(self.buf) if self.hits >= self.sustain else None


def build_model(store):
    """Median measured build seconds per index width (1..3); missing widths scaled linearly."""
    by_w = {}
    for key, s in getattr(store, "build_s", {}).items():
        by_w.setdefault(len(key), []).append(s)
    med = {w: float(np.median(v)) for w, v in by_w.items()}
    per_col = min((s / w for w, s in med.items()), default=1.0)   # seconds per single-column unit
    return lambda w: med.get(w, per_col * w)


def run_scenario(est, bm, name, C, seed, si, qw_levels, horizon, k_fast):
    srng = np.random.default_rng([seed, si, 0])                 # same streams as fir_baselines.py
    dists, onset = F.scenario(name, C, srng)
    T = len(dists)
    wrng = np.random.default_rng([seed, si, 1])
    windows = [F.sample_window(p, wrng) for p in dists]
    init_win = F.sample_window(dists[0], np.random.default_rng([seed, si, 2]))
    init, *_ = F.full_retune(est, init_win)
    jcost = lambda cfg, t: est.score(dists[t], cfg)

    def summarize(pol, cfgs, builds_list, rts, calls, qw=None):
        costs = [jcost(cfgs[t], t)[1] for t in range(T)]
        viols = [jcost(cfgs[t], t)[0] for t in range(T)]
        post = [t for t in rts if t >= onset]
        build_s = float(sum(bm(len(i)) for b in builds_list for i in b))
        row = dict(scenario=name, seed=seed, policy=pol, qw=qw, post_cost=float(np.mean(costs[onset:])),
                   viol_mass=float(np.mean(viols)), retunes=len(rts), false_retunes=sum(t < onset for t in rts),
                   delay=(min(post) - onset) if post else None, builds=int(sum(len(b) for b in builds_list)),
                   build_s=build_s, whatif=int(calls))
        row["total_s"] = {str(q): float(sum(costs) * q / 1000.0 + build_s) for q in qw_levels}
        return row

    rows = []
    # references
    rows.append(summarize("Static", [init] * T, [], [], 0))
    orc_cfgs = [F.full_retune(est, p)[0] for p in dists]
    orc_builds = [orc_cfgs[0] - init] + [orc_cfgs[t] - orc_cfgs[t - 1] for t in range(1, T)]
    rows.append(summarize("Oracle", orc_cfgs, orc_builds, [], 0))

    def loop(detector, decide=None):
        cfg, cfgs, builds, rts, calls = init, [], [], [], 0
        for t in range(T):
            cfgs.append(cfg)
            p = detector.observe(windows[t])
            if p is None:
                continue
            new, _, k, _ = F.fir_retune(est, p, cfg)
            calls += k
            detector.reset(p)
            if decide is not None:
                before = est.calls
                ok = decide(cfg, new, p)
                calls += est.calls - before
                if not ok:
                    continue
            if new != cfg:
                builds.append(new - cfg); rts.append(t); cfg = new
        return cfgs, builds, rts, calls

    win = F.WIN
    mk_frozen = lambda: F.Detector(init_win, np.random.default_rng([seed, si, 3]))
    mk_fast = lambda: FastDetector(init_win, np.random.default_rng([seed, si, 3]), win, 3.0, k_fast)

    c, b, r, k = loop(mk_frozen())
    rows.append(summarize("FIR+detector", c, b, r, k))
    c, b, r, k = loop(mk_fast())
    rows.append(summarize("FIR+fast", c, b, r, k))

    # Full+detector (reference)
    cfg, cfgs, builds, rts, calls = init, [], [], [], 0
    det = mk_frozen()
    for t in range(T):
        cfgs.append(cfg)
        p = det.observe(windows[t])
        if p is None:
            continue
        new, _, kk, _ = F.full_retune(est, p)
        det.reset(p); calls += kk
        if new != cfg:
            builds.append(new - cfg); rts.append(t); cfg = new
    rows.append(summarize("Full+detector", cfgs, builds, rts, calls))

    # Continuous FIR (no detector)
    cfg, cfgs, builds, rts, calls = init, [], [], [], 0
    for t in range(T):
        cfgs.append(cfg)
        new, _, kk, _ = F.fir_retune(est, windows[t], cfg)
        calls += kk
        if new != cfg:
            builds.append(new - cfg); rts.append(t); cfg = new
    rows.append(summarize("Continuous FIR", cfgs, builds, rts, calls))

    # Ski-rental switching variants, one run per traffic level
    def ski_rental(detector, qw):
        cfg, cfgs, builds, rts, calls = init, [], [], [], 0
        prop, rent, idle = None, 0.0, 0
        for t in range(T):
            cfgs.append(cfg)
            w = windows[t]
            p = detector.observe(w)
            if p is not None:
                new, _, kk, _ = F.fir_retune(est, p, cfg)
                calls += kk
                detector.reset(p)
                prop, rent, idle = (new if new != cfg else None), 0.0, 0
            if prop is None:
                continue
            before = est.calls
            vc, cc = est.score(w, cfg)
            vn, cn = est.score(w, prop)
            calls += est.calls - before
            excess = qw * (cc - cn) / 1000.0
            if excess > 0:
                rent += excess; idle = 0
            else:
                idle += 1
            build = sum(bm(len(i)) for i in prop - cfg)
            if (vc > 0 and vn == 0) or rent >= build:
                builds.append(prop - cfg); rts.append(t); cfg = prop
                prop, rent, idle = None, 0.0, 0
            elif idle >= 2:
                prop, rent, idle = None, 0.0, 0
        return cfgs, builds, rts, calls

    for qw in qw_levels:
        c, b, r, k = ski_rental(mk_frozen(), qw)
        rows.append(summarize("FIR+SR", c, b, r, k, qw))
        c, b, r, k = ski_rental(mk_fast(), qw)
        rows.append(summarize("FIR+fast+SR", c, b, r, k, qw))
    return rows


def fast_sweep(est, C, seed, k_values):
    rows = []
    for si, name in enumerate(SCENARIOS):
        srng = np.random.default_rng([seed, si, 0])
        dists, onset = F.scenario(name, C, srng)
        wrng = np.random.default_rng([seed, si, 1])
        windows = [F.sample_window(p, wrng) for p in dists]
        init_win = F.sample_window(dists[0], np.random.default_rng([seed, si, 2]))
        init, *_ = F.full_retune(est, init_win)
        orc = np.mean([est.score(dists[t], F.full_retune(est, dists[t])[0])[1] for t in range(onset, len(dists))])
        for kf in k_values:
            det = FastDetector(init_win, np.random.default_rng([seed, si, 3]), F.WIN, 3.0, kf)
            cfg, costs, rts = init, [], []
            for t, w in enumerate(windows):
                costs.append(est.score(dists[t], cfg)[1])
                p = det.observe(w)
                if p is not None:
                    new = F.fir_retune(est, p, cfg)[0]; det.reset(p)
                    if new != cfg:
                        cfg = new; rts.append(t)
            post = [t for t in rts if t >= onset]
            rows.append(dict(seed=seed, scenario=name, k_fast=kf, false_retunes=sum(t < onset for t in rts),
                             delay=(min(post) - onset) if post else None,
                             regret=float(np.mean(costs[onset:]) / orc - 1)))
    return rows


def pct(xs):
    x = np.asarray(xs, float) * 100
    if len(x) < 2:
        return f"{x.mean():+.1f}%"
    half = B.T95.get(len(x) - 1, 1.96) * x.std(ddof=1) / np.sqrt(len(x))
    return f"{x.mean():+.1f}% [{x.mean() - half:+.1f}, {x.mean() + half:+.1f}]"


def report(rows, sweep, out, label, qw_levels):
    L = [f"# E6 Fast-path detection and cost-aware switching ({label})", "",
         f"K_FAST = {K_FAST}, traffic levels Q_w = {list(qw_levels)} queries/window. "
         "Regret = post-onset estimated query cost vs hindsight re-tune (paired, 95% t-CI). "
         "Total time = query time + index build time (modeled from measured FAISS builds); "
         "'vs FIR' = paired change of total time relative to FIR+detector (negative = better).", ""]
    pols = ["Static", "FIR+detector", "FIR+fast", "Full+detector", "Continuous FIR"]
    for sc in SCENARIOS:
        L += [f"## {sc}", "", "### Query cost", "",
              "| Policy | Regret vs hindsight | Viol. | Re-tunes | False | Delay | Builds | What-if |",
              "|---|---|---|---|---|---|---|---|"]
        orc = {r["seed"]: r["post_cost"] for r in rows if r["scenario"] == sc and r["policy"] == "Oracle"}
        for p in pols + ["FIR+SR", "FIR+fast+SR"]:
            for qw in ([None] if p in pols else qw_levels):
                R = [r for r in rows if r["scenario"] == sc and r["policy"] == p and r["qw"] == qw]
                if not R:
                    continue
                d = [r["delay"] for r in R if r["delay"] is not None]
                name = p if qw is None else f"{p} (Q_w={qw:,})"
                L.append(f"| {name} | {pct([r['post_cost'] / orc[r['seed']] - 1 for r in R])} | "
                         f"{np.mean([r['viol_mass'] for r in R]):.3f} | {np.mean([r['retunes'] for r in R]):.1f} | "
                         f"{np.mean([r['false_retunes'] for r in R]):.1f} | {(np.mean(d) if d else float('nan')):.1f} | "
                         f"{np.mean([r['builds'] for r in R]):.1f} | {np.mean([r['whatif'] for r in R]):.0f} |")
        L += ["", "### Total time (queries + index builds), relative to FIR+detector", "",
              "| Policy | " + " | ".join(f"Q_w={q:,}" for q in qw_levels) + " |",
              "|---|" + "---|" * len(qw_levels)]
        base = {r["seed"]: r["total_s"] for r in rows if r["scenario"] == sc and r["policy"] == "FIR+detector"}
        for p in ["Static", "FIR+fast", "Full+detector", "Continuous FIR", "FIR+SR", "FIR+fast+SR"]:
            cells = []
            for q in qw_levels:
                R = [r for r in rows if r["scenario"] == sc and r["policy"] == p and r["qw"] in (None, q)]
                if p in ("FIR+SR", "FIR+fast+SR"):
                    R = [r for r in R if r["qw"] == q]
                cells.append(pct([r["total_s"][str(q)] / base[r["seed"]][str(q)] - 1 for r in R]))
            L.append(f"| {p} | " + " | ".join(cells) + " |")
        L.append("")
    if sweep:
        L += ["## Fast-path threshold sweep (FIR+fast)", "",
              "| Scenario | K_FAST | False re-tunes | Delay | Regret vs hindsight |", "|---|---|---|---|---|"]
        for sc in SCENARIOS:
            for kf in sorted({r["k_fast"] for r in sweep}):
                R = [r for r in sweep if r["scenario"] == sc and r["k_fast"] == kf]
                d = [r["delay"] for r in R if r["delay"] is not None]
                L.append(f"| {sc} | {kf:g} | {np.mean([r['false_retunes'] for r in R]):.2f} | "
                         f"{(np.mean(d) if d else float('nan')):.2f} ({len(d)}/{len(R)}) | "
                         f"{np.mean([r['regret'] for r in R]) * 100:+.1f}% |")
    out.mkdir(parents=True, exist_ok=True)
    (out / "extensions.md").write_text("\n".join(L), encoding="utf-8")
    json.dump(dict(E6=rows, fast_sweep=sweep), open(out / "extensions.json", "w"), indent=1, default=str)
    print("\n".join(L))


def main():
    global K_FAST, HORIZON
    ap = argparse.ArgumentParser()
    ap.add_argument("--data")
    ap.add_argument("--seeds", nargs="+", type=int)
    ap.add_argument("--out")
    ap.add_argument("--k_fast", type=float, default=K_FAST)
    ap.add_argument("--horizon", type=int, default=HORIZON)
    ap.add_argument("--skip_sweep", action="store_true")
    a = ap.parse_args()
    B.check_api()
    K_FAST, HORIZON = a.k_fast, a.horizon
    C = F.load_real(a.data) if a.data else F.E3_C
    label = f"{Path(a.data).name}, C={C}" if a.data else f"synthetic, C={C}"
    seeds = a.seeds if a.seeds is not None else list(F.SEEDS)
    out = Path(a.out) if a.out else Path(F.OUT) / "extensions"
    rows, sweep, t0 = [], [], time.time()
    for seed in seeds:
        rng = np.random.default_rng(500 + seed)                     # same as fir_baselines.py
        store = F.get_store(F.gen_data(3, rng))
        est = F.Estimator(store, rng, n=80)
        bm = build_model(store)
        for si, sc in enumerate(SCENARIOS):
            rows += run_scenario(est, bm, sc, C, seed, si, QW_LEVELS, HORIZON, K_FAST)
            print(f"[E6 seed {seed}] {sc} done ({time.time() - t0:.0f}s)")
        if not a.skip_sweep:
            sweep += fast_sweep(est, C, seed, (6.0, 10.0, 15.0))
    report(rows, sweep, out, label, QW_LEVELS)
    print(f"\nDone in {time.time() - t0:.0f}s. See {out.resolve()}/extensions.md")


if __name__ == "__main__":
    main()
