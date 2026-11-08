"""P2a analysis (stage2/p2a/P2a_PROTOCOL.md). Charges the tuner term with the C4 times measured in P3
on the same table and applies the pre-registered pass condition.

Usage: python stage2/p2a/p2a_analyze.py coco_30k_4col coco_30k_6col flickr_28k_4col
"""
import json, sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
QW = ("1000", "10000", "100000")
SC = ("abrupt", "gradual", "recurring", "new_type")


def boot(x, rng, B=10_000):
    m = rng.choice(x, size=(B, len(x)), replace=True).mean(1)
    return float(np.mean(x)), float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def main(tables):
    rng = np.random.default_rng(2026)
    out = {}
    for tab in tables:
        rows = json.load(open(ROOT / f"results/p2a/{tab}/p2a.json"))["rows"]
        p3 = json.load(open(ROOT / f"results/p3/{tab}/p3_timing.json"))
        tau = {"i_1ms": 0.001,
               "ii_w_warm": float(np.median([r["warm"]["tune_s"] for r in p3["warm_cold"]])),
               "ii_c_cold": float(np.median([r["cold"]["tune_s"] for r in p3["warm_cold"]]))}
        get = {(r["seed"], r["scenario"], r["policy"], r["qw"]): r for r in rows}
        seeds = sorted({r["seed"] for r in rows})
        res = dict(tuner_cost_s=tau, n_seeds=len(seeds), by_cost={})
        for name, t in tau.items():
            per_q = {}
            for q in QW:
                d_seed, per_sc = [], {s: [] for s in SC}
                for s in seeds:
                    ds = []
                    for sc in SC:
                        f = get[(s, sc, "FIR+fast+SR", int(q))]; c = get[(s, sc, "Continuous+SR", int(q))]
                        tf = f["total_s_no_tuner"][q] + f["tuner_invocations"] * t
                        tc = c["total_s_no_tuner"][q] + c["tuner_invocations"] * t
                        ds.append(tf / tc - 1); per_sc[sc].append(tf / tc - 1)
                    d_seed.append(np.mean(ds))
                m, lo, hi = boot(np.array(d_seed) * 100, rng)
                per_q[q] = dict(mean_pct=m, ci=[lo, hi], pass_=bool(m <= -5 and hi < 0),
                                per_scenario_pct={sc: float(np.mean(v) * 100) for sc, v in per_sc.items()})
            res["by_cost"][name] = per_q
        ctx = {}
        for pol in ("FIR+fast+SR", "Continuous+SR"):
            for q in QW:
                R = [r for r in rows if r["policy"] == pol and r["qw"] == int(q)]
                ctx[f"{pol}@{q}"] = dict(invocations=float(np.mean([r["tuner_invocations"] for r in R])),
                                         switches=float(np.mean([r["switches"] for r in R])),
                                         false_switches=float(np.mean([r["false_switches"] for r in R])),
                                         builds=float(np.mean([r["builds"] for r in R])),
                                         viol_mass=float(np.mean([r["viol_mass"] for r in R])))
        res["context_means_per_run"] = ctx
        res["result"] = "PASS" if all(v["pass_"] for v in res["by_cost"]["ii_w_warm"].values()) else "FAIL"
        out[tab] = res
        print(f"== {tab}  tuner cost (s): " + ", ".join(f"{k}={v:.3f}" for k, v in tau.items()) + f"  -> {res['result']}")
        for name in tau:
            print("  ", name.ljust(10), "  ".join(f"Qw={q}: {v['mean_pct']:+.2f}% [{v['ci'][0]:+.2f}, {v['ci'][1]:+.2f}]{' *' if v['pass_'] else ''}"
                                               for q, v in res["by_cost"][name].items()))
        for k, v in ctx.items():
            print("   ", k.ljust(22), {a: round(b, 2) for a, b in v.items()})
    json.dump(out, open(ROOT / "results/p2a/p2a_summary.json", "w"), indent=1)
    print("pilot:", "PASS" if all(v["result"] == "PASS" for v in out.values()) else "FAIL (so far; COCO-6 full pending)" )


if __name__ == "__main__":
    main(sys.argv[1:])
