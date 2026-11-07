"""
Paired per-seed statistics for FIR-MINT results.

Each seed uses a different workload, so absolute values vary a lot between seeds.
The fair comparison is paired: policy vs. baseline *within the same seed*.

Usage:
  python paired_stats.py <results.json> [<results.json> ...] [--out paired_stats.md]

For every results.json it reports, per seed and aggregated:
  E1: latency and p95 change of FIR-MINT and Full re-tune vs Static, and FIR vs Full
  E3: post-onset cost change vs Static, and FIR+detector vs Full+detector
Negative % = lower latency/cost = better.
"""
import argparse, json
from pathlib import Path
import numpy as np

T95 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262}


def summary(changes):
    x = np.array(changes, float) * 100
    n = len(x)
    m = x.mean()
    sd = x.std(ddof=1) if n > 1 else 0.0
    half = T95.get(n - 1, 1.96) * sd / np.sqrt(n) if n > 1 else 0.0
    wins = int(np.sum(x < 0))
    return f"{m:+.1f}% | [{m - half:+.1f}%, {m + half:+.1f}%] | {wins}/{n}"


def pct(a, b):
    return a / b - 1.0


def e1_section(rows):
    by_seed = {}
    for r in rows:
        by_seed.setdefault(r["seed"], {})[r["policy"]] = r
    seeds = sorted(s for s, d in by_seed.items() if {"Static", "FIR-MINT", "Full re-tune"} <= set(d))
    L = ["### E1 (measured, paired by seed)", "",
         "| Comparison | Metric | Mean change | 95% CI | Seeds better |", "|---|---|---|---|---|"]
    for a, b in (("FIR-MINT", "Static"), ("Full re-tune", "Static"), ("FIR-MINT", "Full re-tune")):
        for metric in ("latency_ms", "p95_ms"):
            ch = [pct(by_seed[s][a][metric], by_seed[s][b][metric]) for s in seeds]
            L.append(f"| {a} vs {b} | {metric.replace('_ms', '')} | {summary(ch)} |")
    L += ["", "Per seed (mean latency, ms):", "", "| Seed | Static | FIR-MINT | Full re-tune | FIR vs Static |",
          "|---|---|---|---|---|"]
    for s in seeds:
        d = by_seed[s]
        L.append(f"| {s} | {d['Static']['latency_ms']:.3f} | {d['FIR-MINT']['latency_ms']:.3f} | "
                 f"{d['Full re-tune']['latency_ms']:.3f} | "
                 f"{pct(d['FIR-MINT']['latency_ms'], d['Static']['latency_ms']) * 100:+.1f}% |")
    return L


def e3_section(rows):
    L = ["### E3 (estimated post-onset cost, paired by seed)", "",
         "| Scenario | Comparison | Mean change | 95% CI | Seeds better |", "|---|---|---|---|---|"]
    for sc in ("abrupt", "gradual", "recurring", "new_type"):
        by_seed = {}
        for r in rows:
            if r["scenario"] == sc:
                by_seed.setdefault(r["seed"], {})[r["policy"]] = r
        seeds = sorted(by_seed)
        if not seeds:
            continue
        for a, b in (("FIR+detector", "Static"), ("Full+detector", "Static"),
                     ("FIR+detector", "Full+detector"), ("FIR+detector", "Full every window")):
            ch = [pct(by_seed[s][a]["post_cost"], by_seed[s][b]["post_cost"]) for s in seeds
                  if a in by_seed[s] and b in by_seed[s]]
            if ch:
                L.append(f"| {sc} | {a} vs {b} | {summary(ch)} |")
    return L


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--out", default="paired_stats.md")
    a = ap.parse_args()
    L = ["# Paired per-seed statistics", "",
         "Negative = lower latency/cost (better). 95% CI uses the t-distribution over seeds. "
         "'Seeds better' counts seeds where the first policy beats the second.", ""]
    for f in a.files:
        d = json.load(open(f, encoding="utf-8"))
        L += [f"## {f}", ""]
        if d.get("E1"):
            L += e1_section(d["E1"]) + [""]
        if d.get("E3"):
            L += e3_section(d["E3"]) + [""]
    Path(a.out).write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
