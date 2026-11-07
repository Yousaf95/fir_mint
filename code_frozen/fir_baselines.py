"""
FIR-MINT baselines (E4) and detector sensitivity (E5).

Imports the frozen fir_mint_v4.py WITHOUT modifying it and reuses its estimator, planner,
tuners, detector, scenarios and data loading. All policies are evaluated with the same
estimator-based cost model as E3, on identical window samples (paired comparison).

E4 policies (per drift scenario, 30 windows):
  Static              initial configuration, never changed
  FIR+detector        FIR-MINT (frozen KL detector + warm-start FIR)                 [ours]
  Full+detector       frozen detector + full re-tune from scratch
  Oracle              full re-tune on the TRUE distribution every window (upper bound, cost not counted)
  Continuous FIR      FIR every window, no detector (COLT-style continuous tuning)
  Cost-trigger+FIR    re-tune when estimated cost of the current configuration on the window rises
                      above a bootstrap threshold (Bruno & Chaudhuri alerter style), same persistence/cooldown
  Capped-full+det.    frozen detector + full re-tune with a what-if budget equal to FIR's mean budget
                      (Wii/Esc-style budget-aware tuning)
  Forecast+FIR        frozen detector; FIR tunes for a linearly extrapolated next-window histogram
                      (QueryBot5000-style forecast-then-tune)
  Robust static       tuned once for the worst case over sampled perturbations of the initial workload
                      (CliffGuard-style min-max); never changed

Metrics: mean and post-onset cost, recall-violating mass, re-tunes, false re-tunes, detection delay,
what-if calls (tuning + monitoring), index builds, and paired regret vs Oracle.

E5: FIR+detector sensitivity over window size {150, 300, 600} x threshold k*sigma {2, 3, 4}.

Usage (run from the folder containing the frozen fir_mint_v4.py, or set PYTHONPATH):
  python fir_baselines.py                    # synthetic, C = F.E3_C columns
  python fir_baselines.py --data <vectors>   # real data (same folder format as fir_mint_v4.py --data)
  python fir_baselines.py --seeds 0 1        # subset of seeds (default: F.SEEDS)
  python fir_baselines.py --skip_sensitivity
"""
import argparse, json, time
from pathlib import Path
import numpy as np
import fir_mint_v4 as F

REQUIRED = ["Estimator", "get_store", "gen_data", "scenario", "sample_window", "kl", "full_retune",
            "fir_retune", "Detector", "storage", "candidate_universe", "EXTRA_BUDGET", "SEEDS",
            "WIN", "load_real", "E3_C"]
SCENARIOS = ("abrupt", "gradual", "recurring", "new_type")
POLICIES = ("Static", "FIR+detector", "Full+detector", "Oracle", "Continuous FIR", "Cost-trigger+FIR",
            "Capped-full+det.", "Forecast+FIR", "Robust static")
T95 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262}


def check_api():
    missing = [a for a in REQUIRED if not hasattr(F, a)]
    if missing:
        raise SystemExit(f"fir_mint_v4.py is missing required names: {missing}. "
                         "Stop and report; do not modify the frozen code.")


# ---------------------------------------------------------------- helpers
def smooth(p, eps=1e-3):
    keys = list(p)
    a = np.array([p[k] for k in keys]) + eps
    return dict(zip(keys, a / a.sum()))


def pooled(wins):
    return {k: float(np.mean([w[k] for w in wins])) for k in wins[0]}


def capped_full(est, dist, budget):
    """Greedy full re-tune from scratch, stopped when the what-if budget is spent.
    Candidates are visited in descending workload frequency (best cheap ordering)."""
    est.calls, est.cache = 0, {}
    cands = sorted(F.candidate_universe(dist), key=lambda q: -dist.get(q, 0.0))
    cfg = frozenset()
    best = est.score(dist, cfg)
    while est.calls < budget:
        trials = []
        for c in cands:
            if est.calls >= budget:
                break
            if c in cfg or F.storage(cfg | {c}) > F.EXTRA_BUDGET:
                continue
            trials.append((est.score(dist, cfg | {c}), c))
        if not trials:
            break
        s, c = min(trials, key=lambda t: t[0])
        if s >= best:
            break
        cfg, best = cfg | {c}, s
    return cfg, est.calls


def robust_static(est, p0, rng, K=20, conc=30.0):
    """Min-max greedy over K Dirichlet perturbations of the initial workload."""
    keys = list(p0)
    base = np.array([p0[k] for k in keys]) + 1e-3
    base /= base.sum()
    samples = [dict(zip(keys, rng.dirichlet(base * conc))) for _ in range(K)]
    union = {k: max(s[k] for s in samples) for k in keys}
    cands = F.candidate_universe(union)
    est.calls, est.cache = 0, {}

    def obj(cfg):
        sc = [est.score(s, cfg) for s in samples]
        return (max(v for v, _ in sc), max(c for _, c in sc))

    cfg, best = frozenset(), obj(frozenset())
    while True:
        trials = [(obj(cfg | {c}), c) for c in cands
                  if c not in cfg and F.storage(cfg | {c}) <= F.EXTRA_BUDGET]
        if not trials:
            break
        s, c = min(trials, key=lambda t: t[0])
        if s >= best:
            break
        cfg, best = cfg | {c}, s
    return cfg, est.calls


def forecast(history):
    """Linear extrapolation of the per-type share over the last 3 windows (clipped, renormalized)."""
    if len(history) < 3:
        return history[-1]
    a, b = history[-3], history[-1]
    f = {k: max(0.0, b[k] + (b[k] - a[k]) / 2.0) for k in b}
    s = sum(f.values())
    return {k: v / s for k, v in f.items()} if s > 0 else b


class ParamDetector:
    """Same logic as the frozen F.Detector, with configurable window size and k*sigma threshold."""

    def __init__(self, ref, rng, win, k_sigma, sustain=2, cooldown=2):
        self.rng, self.win, self.k, self.sustain, self.cooldown = rng, win, k_sigma, sustain, cooldown
        self.reset(ref)

    def reset(self, ref):
        self.ref, self.hits, self.cool, self.buf = ref, 0, self.cooldown, []
        sm = smooth(ref)
        s = [F.kl(F.sample_window(sm, self.rng, n=self.win), F.sample_window(sm, self.rng, n=self.win))
             for _ in range(300)]
        self.thr = float(np.mean(s) + self.k * np.std(s))

    def observe(self, w):
        if self.cool > 0:
            self.cool -= 1
            return None
        if F.kl(w, self.ref) > self.thr:
            self.hits += 1; self.buf.append(w)
        else:
            self.hits, self.buf = 0, []
        return pooled(self.buf) if self.hits >= self.sustain else None


class CostTrigger:
    """Alerter: fire when the estimated cost of the current config on the window exceeds a bootstrap
    threshold around its cost on the reference window (or when recall would be violated)."""

    def __init__(self, est, ref, cfg, rng, k_sigma=3.0, sustain=2, cooldown=2):
        self.est, self.rng, self.k, self.sustain, self.cooldown = est, rng, k_sigma, sustain, cooldown
        self.calls = 0
        self.reset(ref, cfg)

    def _score(self, dist, cfg):
        before = self.est.calls
        out = self.est.score(dist, cfg)
        self.calls += self.est.calls - before
        return out

    def reset(self, ref, cfg):
        self.cfg, self.hits, self.cool, self.buf = cfg, 0, self.cooldown, []
        sm = smooth(ref)
        costs = [self._score(F.sample_window(sm, self.rng), cfg)[1] for _ in range(100)]
        self.thr = float(np.mean(costs) + self.k * np.std(costs))

    def observe(self, w):
        if self.cool > 0:
            self.cool -= 1
            return None
        v, c = self._score(w, self.cfg)
        if v > 0 or c > self.thr:
            self.hits += 1; self.buf.append(w)
        else:
            self.hits, self.buf = 0, []
        return pooled(self.buf) if self.hits >= self.sustain else None


# ---------------------------------------------------------------- one scenario, all policies
def run_scenario(est, name, C, seed, sc_idx, fir_budget):
    srng = np.random.default_rng([seed, sc_idx, 0])
    dists, onset = F.scenario(name, C, srng)
    T = len(dists)
    wrng = np.random.default_rng([seed, sc_idx, 1])
    windows = [F.sample_window(p, wrng) for p in dists]              # identical windows for all policies
    init_win = F.sample_window(dists[0], np.random.default_rng([seed, sc_idx, 2]))
    init, *_ = F.full_retune(est, init_win)
    true_cost = lambda cfg, t: est.score(dists[t], cfg)

    out = {}

    def record(pol, cfgs, calls, builds, retunes):
        costs, viols = zip(*[(true_cost(cfgs[t], t)[1], true_cost(cfgs[t], t)[0]) for t in range(T)])
        post = [t for t in retunes if t >= onset]
        out[pol] = dict(scenario=name, seed=seed, policy=pol, costs=list(costs),
                        mean_cost=float(np.mean(costs)), post_cost=float(np.mean(costs[onset:])),
                        viol_mass=float(np.mean(viols)), whatif=int(calls), builds=int(builds),
                        retunes=len(retunes), false_retunes=sum(t < onset for t in retunes),
                        delay=(min(post) - onset) if post else None)

    # Static
    record("Static", [init] * T, 0, 0, [])

    # Oracle (true distribution, every window; tuning cost not counted)
    record("Oracle", [F.full_retune(est, p)[0] for p in dists], 0, 0, [])

    # Detector-driven policies (frozen detector), possibly with different tuners
    def detector_policy(tune):
        drng = np.random.default_rng([seed, sc_idx, 3])
        det = F.Detector(init_win, drng)
        cfg, cfgs, calls, builds, rts, hist = init, [], 0, 0, [], []
        for t in range(T):
            cfgs.append(cfg)
            hist.append(windows[t])
            p = det.observe(windows[t])
            if p is None:
                continue
            new, k = tune(p, cfg, hist)
            det.reset(p)
            calls += k; builds += len(new - cfg); cfg = new; rts.append(t)
        return cfgs, calls, builds, rts

    fir_calls_per_retune = []

    def tune_fir(p, cfg, hist):
        new, _, k, _ = F.fir_retune(est, p, cfg)
        fir_calls_per_retune.append(k)
        return new, k

    record("FIR+detector", *detector_policy(tune_fir))
    def tune_full(p, cfg, hist):
        new, _, k, _ = F.full_retune(est, p)
        return new, k

    record("Full+detector", *detector_policy(tune_full))
    budget = fir_budget if fir_budget else (np.mean(fir_calls_per_retune) if fir_calls_per_retune else 50)
    record("Capped-full+det.", *detector_policy(lambda p, cfg, h: capped_full(est, p, budget)))

    def tune_forecast(p, cfg, hist):
        new, _, k, _ = F.fir_retune(est, forecast(hist), cfg)
        return new, k

    record("Forecast+FIR", *detector_policy(tune_forecast))

    # Continuous FIR (no detector)
    cfg, cfgs, calls, builds, rts = init, [], 0, 0, []
    for t in range(T):
        cfgs.append(cfg)
        new, _, k, _ = F.fir_retune(est, windows[t], cfg)
        calls += k
        if new != cfg:
            builds += len(new - cfg); rts.append(t); cfg = new
    record("Continuous FIR", cfgs, calls, builds, rts)

    # Cost-trigger + FIR
    trig = CostTrigger(est, init_win, init, np.random.default_rng([seed, sc_idx, 4]))
    cfg, cfgs, calls, builds, rts = init, [], 0, 0, []
    for t in range(T):
        cfgs.append(cfg)
        p = trig.observe(windows[t])
        if p is None:
            continue
        new, _, k, _ = F.fir_retune(est, p, cfg)
        calls += k; builds += len(new - cfg); cfg = new; rts.append(t)
        trig.reset(p, cfg)
    record("Cost-trigger+FIR", cfgs, calls + trig.calls, builds, rts)

    # Robust static
    rob, k = robust_static(est, init_win, np.random.default_rng([seed, sc_idx, 5]))
    record("Robust static", [rob] * T, k, len(rob - init), [])

    return [out[p] for p in POLICIES]


def run_sensitivity(est, C, seed):
    rows = []
    for si, name in enumerate(SCENARIOS):
        srng = np.random.default_rng([seed, si, 0])
        dists, onset = F.scenario(name, C, srng)
        init_win = F.sample_window(dists[0], np.random.default_rng([seed, si, 2]))
        init, *_ = F.full_retune(est, init_win)
        oracle_post = np.mean([est.score(dists[t], F.full_retune(est, dists[t])[0])[1]
                               for t in range(onset, len(dists))])
        for win in (150, 300, 600):
            wrng = np.random.default_rng([seed, si, 10 + win])
            windows = [F.sample_window(p, wrng, n=win) for p in dists]
            for k_sig in (2.0, 3.0, 4.0):
                det = ParamDetector(F.sample_window(dists[0], np.random.default_rng([seed, si, 11]), n=win),
                                    np.random.default_rng([seed, si, 12]), win, k_sig)
                cfg, costs, rts = init, [], []
                for t, w in enumerate(windows):
                    costs.append(est.score(dists[t], cfg)[1])
                    p = det.observe(w)
                    if p is not None:
                        cfg = F.fir_retune(est, p, cfg)[0]; det.reset(p); rts.append(t)
                post = [t for t in rts if t >= onset]
                rows.append(dict(seed=seed, scenario=name, window=win, k_sigma=k_sig,
                                 false_retunes=sum(t < onset for t in rts), retunes=len(rts),
                                 delay=(min(post) - onset) if post else None,
                                 regret=float(np.mean(costs[onset:]) / oracle_post - 1)))
    return rows


# ---------------------------------------------------------------- reporting
def ci(x):
    x = np.asarray(x, float) * 100
    n = len(x)
    if n < 2:
        return f"{x.mean():+.1f}%", ""
    half = T95.get(n - 1, 1.96) * x.std(ddof=1) / np.sqrt(n)
    return f"{x.mean():+.1f}%", f"[{x.mean() - half:+.1f}, {x.mean() + half:+.1f}]"


def report(rows, sens, out, label):
    L = [f"# E4 Baselines and E5 detector sensitivity ({label})", "",
         "Estimator-based cost (same model as E3), identical window samples for all policies. "
         "Regret = post-onset cost relative to Oracle (paired by seed, 95% t-CI). "
         "vs FIR = post-onset cost relative to FIR+detector (negative = better than FIR). "
         "Delay = windows from drift onset to the first re-tune.", ""]
    for sc in SCENARIOS:
        L += [f"## {sc}", "",
              "| Policy | Post-onset cost (ms) | Regret vs Oracle | 95% CI | vs FIR | 95% CI | Viol. mass | "
              "Re-tunes | False | Delay | What-if | Builds |",
              "|---|---|---|---|---|---|---|---|---|---|---|---|"]
        by = {p: [r for r in rows if r["scenario"] == sc and r["policy"] == p] for p in POLICIES}
        seeds = sorted({r["seed"] for r in by["Oracle"]})
        for p in POLICIES:
            R = sorted(by[p], key=lambda r: r["seed"])
            orc = {r["seed"]: r["post_cost"] for r in by["Oracle"]}
            fir = {r["seed"]: r["post_cost"] for r in by["FIR+detector"]}
            reg, reg_ci = ci([r["post_cost"] / orc[r["seed"]] - 1 for r in R])
            vf, vf_ci = ci([r["post_cost"] / fir[r["seed"]] - 1 for r in R]) if p != "FIR+detector" else ("—", "")
            d = [r["delay"] for r in R if r["delay"] is not None]
            delay = f"{np.mean(d):.1f}" if d else "—"
            L.append(f"| {p} | {np.mean([r['post_cost'] for r in R]):.3f} ± {np.std([r['post_cost'] for r in R]):.3f} | "
                     f"{reg} | {reg_ci} | {vf} | {vf_ci} | {np.mean([r['viol_mass'] for r in R]):.3f} | "
                     f"{np.mean([r['retunes'] for r in R]):.1f} | {np.mean([r['false_retunes'] for r in R]):.1f} | "
                     f"{delay} | {np.mean([r['whatif'] for r in R]):.0f} | {np.mean([r['builds'] for r in R]):.1f} |")
        L.append("")
    if sens:
        L += ["## E5 Detector sensitivity (FIR+detector)", "",
              "| Scenario | Window | k·σ | False re-tunes | Re-tunes | Delay | Regret vs Oracle |",
              "|---|---|---|---|---|---|---|"]
        for sc in SCENARIOS:
            for win in (150, 300, 600):
                for k in (2.0, 3.0, 4.0):
                    R = [r for r in sens if r["scenario"] == sc and r["window"] == win and r["k_sigma"] == k]
                    d = [r["delay"] for r in R if r["delay"] is not None]
                    L.append(f"| {sc} | {win} | {k:.0f} | {np.mean([r['false_retunes'] for r in R]):.1f} | "
                             f"{np.mean([r['retunes'] for r in R]):.1f} | "
                             f"{(np.mean(d) if d else float('nan')):.1f} ({len(d)}/{len(R)} detected) | "
                             f"{np.mean([r['regret'] for r in R]) * 100:+.1f}% |")
    out.mkdir(parents=True, exist_ok=True)
    (out / "baselines.md").write_text("\n".join(L), encoding="utf-8")
    json.dump(dict(E4=rows, E5=sens), open(out / "baselines.json", "w"), indent=1, default=str)
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(1, 4, figsize=(16, 4), sharey=True)
        pols = [p for p in POLICIES if p != "Oracle"]
        for a, sc in zip(ax, SCENARIOS):
            orc = {r["seed"]: r["post_cost"] for r in rows if r["scenario"] == sc and r["policy"] == "Oracle"}
            vals = [[(r["post_cost"] / orc[r["seed"]] - 1) * 100 for r in rows
                     if r["scenario"] == sc and r["policy"] == p] for p in pols]
            a.barh(pols, [np.mean(v) for v in vals], xerr=[np.std(v) for v in vals],
                   color=["#d9822b" if p == "FIR+detector" else "#9aa5b1" for p in pols])
            a.set_title(sc.replace("_", " ")); a.set_xlabel("Post-onset regret vs Oracle (%)")
            a.invert_yaxis()
        fig.tight_layout(); fig.savefig(out / "fig5_baselines.png", dpi=200); plt.close(fig)
    except Exception as e:  # plotting must never invalidate results
        print("plot skipped:", e)
    print("\n".join(L))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", help="real vector folder (as for fir_mint_v4.py --data)")
    ap.add_argument("--seeds", nargs="+", type=int)
    ap.add_argument("--skip_sensitivity", action="store_true")
    ap.add_argument("--out", help="output folder (default: <fir_mint_v4 OUT>/baselines)")
    a = ap.parse_args()
    check_api()
    C = F.load_real(a.data) if a.data else F.E3_C
    label = f"{Path(a.data).name}, C={C}" if a.data else f"synthetic, C={C}"
    seeds = a.seeds if a.seeds is not None else list(F.SEEDS)
    out = Path(a.out) if a.out else Path(F.OUT) / "baselines"
    rows, sens, t0 = [], [], time.time()
    for seed in seeds:
        rng = np.random.default_rng(500 + seed)
        est = F.Estimator(F.get_store(F.gen_data(3, rng)), rng, n=80)
        for si, sc in enumerate(SCENARIOS):
            rows += run_scenario(est, sc, C, seed, si, None)
            print(f"[E4 seed {seed}] {sc} done ({time.time() - t0:.0f}s)")
        if not a.skip_sensitivity:
            sens += run_sensitivity(est, C, seed)
            print(f"[E5 seed {seed}] done ({time.time() - t0:.0f}s)")
    report(rows, sens, out, label)
    print(f"\nDone in {time.time() - t0:.0f}s. See {out.resolve()}/baselines.md")


if __name__ == "__main__":
    main()
