"""Per-seed tables for status report 2 (Reply 1, Part 3.4 format where it applies).

Reads results/p3/*/p3*.json and results/p2a/*/p2a.json; writes stage2/STATUS_REPORT2_TABLES.md.
Usage (repository root): python stage2/report2_tables.py
"""
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
P3 = [("laion_1m_4col", "p3.json", "LAION-1M-4"), ("coco_full_6col", "p3_timing.json", "COCO-6 full (117k)"),
      ("coco_30k_4col", "p3_timing.json", "COCO-4 30k"), ("coco_30k_6col", "p3_timing.json", "COCO-6 30k"),
      ("flickr_28k_4col", "p3_timing.json", "Flickr30k-4 28k")]
P2A = [("coco_30k_4col", "COCO-4 30k"), ("coco_30k_6col", "COCO-6 30k"), ("flickr_28k_4col", "Flickr30k-4 28k"),
       ("coco_full_6col", "COCO-6 full (117k)")]
QW = (1000, 10000, 100000)
SC = ("abrupt", "gradual", "recurring", "new_type")
cfg = lambda c: sorted(tuple(x) for x in c)


def p3_section(L):
    L.append("## P3: C4 tuner cost per seed (measured, wall clock, single-threaded planner)\n")
    L.append("Cold = tune the drifted workload from scratch; warm = re-tune it starting from the stable "
             "configuration with the planner cache kept. Calibration is one-time and excluded (reported in "
             "P3_REPORT.md). 'Config moved' = the drifted workload's configuration differs from the stable one.\n")
    for tab, fn, name in P3:
        p = json.load(open(ROOT / f"results/p3/{tab}/{fn}"))
        L.append(f"### {name}\n")
        L.append("| Seed | Cold tuning (s) | Warm re-tune (s) | Cut (tuning only) | Warm cost / cold cost - 1 | "
                 "Planner calls cold / warm | Config moved | Warm = cold config |")
        L.append("|---:|---:|---:|---:|---:|---|---|---|")
        cuts = []
        for r in p["warm_cold"]:
            c, w, s = r["cold"], r["warm"], r["stable"]
            cut = 1 - w["tune_s"] / c["tune_s"]; cuts.append(cut)
            L.append(f"| {r['seed']} | {c['tune_s']:.2f} | {w['tune_s']:.3f} | {cut*100:.1f}% | "
                     f"{(w['cost']/c['cost']-1)*100:+.3f}% | {c['planner_calls']} / {w['planner_calls']} | "
                     f"{'yes' if cfg(c['config']) != cfg(s['config']) else 'no'} | "
                     f"{'yes' if cfg(c['config']) == cfg(w['config']) else 'no'} |")
        L.append(f"\nMedian cut {np.median(cuts)*100:.1f}%; 5 repeats of seed 0 cold: "
                 + ", ".join(f"{x:.2f}" for x in p["repeat_seed0"]) + " s.\n")


def boot(x, rng, B=10_000):
    m = rng.choice(x, size=(B, len(x)), replace=True).mean(1)
    return float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def p2a_section(L):
    S = json.load(open(ROOT / "results/p2a/p2a_summary.json"))
    L.append("## P2a: FIR+fast+SR against Continuous+SR per seed (estimated query time; measured build "
             "model and tuner cost)\n")
    L.append("d = mean over the four scenarios of (FIR total / Continuous total - 1), tuner term charged at "
             "the C4 warm re-tune time of the same table (setting ii-w, the gated one). Firings = detector "
             "firings summed over the four scenarios (Continuous re-tunes 4 x 30 = 120 times). Switches, "
             "builds and build seconds are summed over the four scenarios. Recall columns of Part 3.4 do not "
             "apply: the frozen simulator gives estimated violating mass only (last column, mean over "
             "policies, identical for both).\n")
    for tab, name in P2A:
        rows = json.load(open(ROOT / f"results/p2a/{tab}/p2a.json"))["rows"]
        tau = S[tab]["tuner_cost_s"]["ii_w_warm"]
        get = {(r["seed"], r["scenario"], r["policy"], r["qw"]): r for r in rows}
        seeds = sorted({r["seed"] for r in rows})
        L.append(f"### {name} (warm tuner cost {tau:.3f} s per invocation)\n")
        L.append("| Seed | d @ 1k | d @ 10k | d @ 100k | Firings | Switches FIR / Cont @ 10k | "
                 "Switches FIR / Cont @ 100k | False switches Cont @ 100k | Build s FIR / Cont @ 10k | Viol. mass |")
        L.append("|---:|---:|---:|---:|---:|---|---|---:|---|---:|")
        D = {q: [] for q in QW}
        for s in seeds:
            ds = {}
            for q in QW:
                v = []
                for sc in SC:
                    f, c = get[(s, sc, "FIR+fast+SR", q)], get[(s, sc, "Continuous+SR", q)]
                    tf = f["total_s_no_tuner"][str(q)] + f["tuner_invocations"] * tau
                    tc = c["total_s_no_tuner"][str(q)] + c["tuner_invocations"] * tau
                    v.append(tf / tc - 1)
                ds[q] = np.mean(v) * 100; D[q].append(ds[q])
            sm = lambda pol, q, k: sum(get[(s, sc, pol, q)][k] for sc in SC)
            vm = np.mean([get[(s, sc, "Static", None)]["viol_mass"] for sc in SC])
            L.append(f"| {s} | {ds[1000]:+.2f}% | {ds[10000]:+.2f}% | {ds[100000]:+.2f}% | "
                     f"{sm('FIR+fast+SR', 10000, 'tuner_invocations')} | "
                     f"{sm('FIR+fast+SR', 10000, 'switches')} / {sm('Continuous+SR', 10000, 'switches')} | "
                     f"{sm('FIR+fast+SR', 100000, 'switches')} / {sm('Continuous+SR', 100000, 'switches')} | "
                     f"{sm('Continuous+SR', 100000, 'false_switches')} | "
                     f"{sm('FIR+fast+SR', 10000, 'build_s'):.1f} / {sm('Continuous+SR', 10000, 'build_s'):.1f} | "
                     f"{vm:.3f} |")
        L.append("")
        L.append("| Q_w | Mean d | 95% bootstrap CI | Seeds with d < 0 | Sign-test p (two-sided) | Pass (d <= -5% and CI upper < 0) |")
        L.append("|---:|---:|---|---:|---:|---|")
        for q in QW:
            v = S[tab]["by_cost"]["ii_w_warm"][str(q)]
            neg = sum(x < 0 for x in D[q]); n = sum(x != 0 for x in D[q])
            p = sign_p(neg, n)
            L.append(f"| {q:,} | {v['mean_pct']:+.2f}% | [{v['ci'][0]:+.2f}, {v['ci'][1]:+.2f}] | {neg} of {len(D[q])} | "
                     f"{p:.2g} | {'PASS' if v['pass_'] else 'FAIL'} |")
        L.append(f"\nTable result: **{S[tab]['result']}**.\n")


def sign_p(k, n):
    from math import comb
    if n == 0:
        return 1.0
    t = min(k, n - k)
    return min(1.0, 2 * sum(comb(n, i) for i in range(t + 1)) / 2 ** n)


def main():
    L = ["# Status report 2: per-seed tables\n",
         "Generated by `stage2/report2_tables.py` from the result files. Companion to `STATUS_REPORT2.md`.\n"]
    p3_section(L); p2a_section(L)
    (ROOT / "stage2/STATUS_REPORT2_TABLES.md").write_text("\n".join(L) + "\n")
    print("wrote stage2/STATUS_REPORT2_TABLES.md")


if __name__ == "__main__":
    main()
