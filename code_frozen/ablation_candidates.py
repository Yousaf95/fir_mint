"""
Ablation: FIR candidate count K vs. tuning effort and solution quality.
Estimator-based, abrupt drift, no what-if cache (every plan estimate counted).
Requires fir_mint_v4.py in the same folder.
"""
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import fir_mint_v4 as F

F.USE_CACHE = False
SETTINGS = [("K=1", 1, 1), ("K=2", 2, 2), ("K=3", 3, 3), ("K=5", 5, 5), ("K=8", 8, 8),
            ("K=12", 12, 12), ("Adaptive (3..8, 80%)", 3, 8)]
COLS = (6, 8, 12)


def main():
    rows = []
    for seed in F.SEEDS:
        rng = np.random.default_rng(300 + seed)
        est = F.Estimator(F.Store(F.gen_data(3, rng)), rng, n=80)
        for C in COLS:
            p0, p1 = F.zipf_dist(C, rng, 0.85), F.zipf_dist(C, rng, 0.35)
            static, *_ = F.full_retune(est, p0)
            obs = F.sample_window(p1, rng, n=2 * F.WIN)
            full, _, fc, _ = F.full_retune(est, obs)
            _, full_cost = est.score(p1, full)
            _, static_cost = est.score(p1, static)
            for name, kmin, kmax in SETTINGS:
                F.FIR_KMIN, F.FIR_KMAX = kmin, kmax
                fir, _, c, _ = F.fir_retune(est, obs, static)
                v, cost = est.score(p1, fir)
                rows.append(dict(seed=seed, C=C, setting=name, calls=c, full_calls=fc,
                                 cost_ratio=cost / full_cost, static_ratio=static_cost / full_cost, viol=v))
        print(f"seed {seed} done")

    lines = ["# Ablation: FIR candidate count", "",
             "Cost ratio = workload cost of FIR's configuration / full re-tune (1.00 = same quality). "
             "Gap closed = share of the static-vs-full cost gap that FIR recovers. Mean over 5 seeds.", ""]
    for C in COLS:
        lines += [f"## {C} columns", "",
                  "| FIR setting | What-if calls | Full calls | Speed-up | Cost ratio | Gap closed |",
                  "|---|---|---|---|---|---|"]
        for name, *_ in SETTINGS:
            R = [r for r in rows if r["C"] == C and r["setting"] == name]
            gap = np.mean([(r["static_ratio"] - r["cost_ratio"]) / max(r["static_ratio"] - 1, 1e-9) for r in R])
            lines.append(f"| {name} | {np.mean([r['calls'] for r in R]):.0f} | "
                         f"{np.mean([r['full_calls'] for r in R]):.0f} | "
                         f"{np.mean([r['full_calls'] / r['calls'] for r in R]):.1f}× | "
                         f"{np.mean([r['cost_ratio'] for r in R]):.3f} | {gap * 100:.0f}% |")
        lines.append("")
    (F.OUT / "ablation_candidates.md").write_text("\n".join(lines), encoding="utf-8")
    json.dump(rows, open(F.OUT / "ablation_candidates.json", "w"), indent=1)

    fig, ax = plt.subplots(1, len(COLS), figsize=(13, 3.8), sharey=True)
    for a, C in zip(ax, COLS):
        for name, *_ in SETTINGS:
            R = [r for r in rows if r["C"] == C and r["setting"] == name]
            x = np.mean([r["full_calls"] / r["calls"] for r in R])
            y = np.mean([r["cost_ratio"] for r in R])
            a.scatter(x, y, s=40, c="#2b6cb0" if name.startswith("Adaptive") else "#d9822b")
            a.annotate(name.split(" ")[0], (x, y), textcoords="offset points", xytext=(5, 4), fontsize=8)
        a.axhline(1, ls="--", c="k", lw=0.8)
        a.set_xscale("log"); a.set_title(f"{C} columns")
        a.set_xlabel("Speed-up vs full re-tune (what-if calls, log)")
    ax[0].set_ylabel("Workload cost / full re-tune")
    fig.tight_layout(); fig.savefig(F.OUT / "fig4_ablation_candidates.png", dpi=200); plt.close(fig)
    print("\n".join(lines))


if __name__ == "__main__":
    main()
