"""Stage 1 trace: recompute every number of draft v1.0 from the result files.

Usage:  python stage1/trace.py            (run from the repository root)
Output: stage1/trace_table.csv  (one row per printed number)
        stage1/trace_report.md  (the same table plus per-seed detail)

Formulas follow the frozen v1.0 code:
  paired change  = mean over seeds of (a/b - 1), 95% t-interval (paired_stats.py)
  regret         = post-onset mean cost / Oracle post-onset mean cost - 1, per seed,
                   then mean over seeds (fir_baselines.py line 306)
  min_recall     = min over query types of the mean per-query recall of that type
                   (fir_mint_v4.py lines 439-448)
A printed number "matches" if the recomputed value rounds to it at the printed precision.
"""
import csv
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
T95 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776}
SC = ("abrupt", "gradual", "recurring", "new_type")
ONSET = 10

SRC = {
    "e1": {
        "COCO-4 (CPU host)": "results/fir_mint_v4_results_coco_30k_4col/results.json",
        "COCO-4 (H100 host)": "fir_mint_v4_results_coco_30k_4col_gpu/results.json",
        "COCO-6": "FINAL_RESULTS/coco6/results.json",
        "Flickr30k-4": "FINAL_RESULTS/flickr4/results.json",
        "Synthetic-4": "runs/synthetic/fir_mint_v4_results/results.json",
    },
    "base": {k: f"FINAL_RESULTS/baselines/{v}/baselines.json"
             for k, v in (("Flickr30k-4", "flickr4"), ("COCO-4", "coco4"),
                          ("COCO-6", "coco6"), ("Synthetic", "synthetic"))},
    "ext": {"Flickr30k-4": "FINAL_RESULTS/extensions/flickr4/extensions.json",
            "COCO-4": "FINAL_RESULTS/extensions/coco4/extensions.json",
            "COCO-6": "FINAL_RESULTS/extensions/coco6/extensions.json",
            "Synthetic-5": "FINAL_RESULTS/extensions/synthetic/extensions_synthetic.json"},
    "abl": "runs/synthetic/fir_mint_v4_results/ablation_candidates.json",
    "pilot": "runs/pilot_mint_flickr/pilot.json",
}

rows = []
detail = []


def load(p):
    return json.load(open(ROOT / p, encoding="utf-8"))


def paired(a, b):
    x = (np.asarray(a, float) / np.asarray(b, float) - 1) * 100
    n = len(x)
    h = T95[n - 1] * x.std(ddof=1) / np.sqrt(n)
    return x.mean(), x.mean() - h, x.mean() + h, x


def add(place, claim, value, source, field, decimals=1, note=""):
    """Record one printed number. claim is the printed value (float) or None if text-only."""
    if value is None:
        status = "not traced"
    elif claim is None:
        status = "info"
    else:
        status = "match" if abs(round(value, decimals) - claim) < 10 ** (-decimals) / 2 + 1e-9 else "MISMATCH"
    rows.append(dict(place=place, printed=claim, recomputed=None if value is None else round(value, 4),
                     status=status, source=source, field=field, note=note))


def add_range(place, lo, hi, values, source, field, decimals=1, note=""):
    v = np.asarray(values, float)
    add(place + " (low end)", lo, float(v.min()), source, field, decimals, note)
    add(place + " (high end)", hi, float(v.max()), source, field, decimals, note)


def by(rows_, *keys):
    out = {}
    for r in rows_:
        out[tuple(r[k] for k in keys)] = r
    return out


# ---------------------------------------------------------------- Table II (E1)
T2 = {"COCO-4 (CPU host)": (2.647, 1.999, 2.056, -19.2, -49.5, 11.0, 0.995),
      "COCO-4 (H100 host)": (2.866, 2.498, 2.417, -12.9, -18.3, -7.5, 0.995),
      "COCO-6": (4.911, 4.211, 4.034, -13.2, -29.3, 3.0, 0.969),
      "Flickr30k-4": (1.789, 1.494, 1.481, -14.9, -29.6, -0.3, 0.993),
      "Synthetic-4": (0.633, 0.517, 0.516, -18.3, -28.4, -8.2, None)}
fir_vs_full_e1 = []
for ds, src in SRC["e1"].items():
    E1 = load(src)["E1"]
    t = by(E1, "seed", "policy")
    seeds = sorted({r["seed"] for r in E1})
    lat = {p: [t[(s, p)]["latency_ms"] for s in seeds] for p in ("Static", "FIR-MINT", "Full re-tune")}
    c = T2[ds]
    add(f"Table II {ds} Static", c[0], np.mean(lat["Static"]), src, "E1.latency_ms mean", 3)
    add(f"Table II {ds} FIR-MINT", c[1], np.mean(lat["FIR-MINT"]), src, "E1.latency_ms mean", 3)
    add(f"Table II {ds} Full", c[2], np.mean(lat["Full re-tune"]), src, "E1.latency_ms mean", 3)
    m, lo, hi, per = paired(lat["FIR-MINT"], lat["Static"])
    add(f"Table II {ds} FIR vs Static %", c[3], m, src, "paired a/b-1")
    add(f"Table II {ds} CI low", c[4], lo, src, "t-interval")
    add(f"Table II {ds} CI high", c[5], hi, src, "t-interval")
    detail.append(f"E1 {ds}: FIR vs Static per seed % = {np.round(per, 1).tolist()}")
    mr = [t[(s, 'FIR-MINT')]['min_recall'] for s in seeds]
    allmr = [t[(s, p)]['min_recall'] for s in seeds for p in ("Static", "FIR-MINT", "Full re-tune")]
    add(f"Table II {ds} Min recall", c[6], float(np.mean(mr)), src,
        "mean over seeds of FIR-MINT min over types of per-type mean recall", 3,
        f"per-seed FIR {np.round(mr, 3).tolist()}; lowest over all policies and seeds {min(allmr):.3f}")
    fvf = paired(lat["FIR-MINT"], lat["Full re-tune"])[0]
    fir_vs_full_e1.append(fvf)
    if ds == "Flickr30k-4":
        p95 = {p: [t[(s, p)]["p95_ms"] for s in seeds] for p in ("Static", "FIR-MINT")}
        add("VII-A Flickr30k p95 FIR vs Static %", -21.6, paired(p95["FIR-MINT"], p95["Static"])[0], src, "E1.p95_ms paired")
add_range("VII-A FIR vs Full measured %", -3.0, 5.1, fir_vs_full_e1, "E1 files", "paired FIR/Full-1")

# ---------------------------------------------------------------- Table III (E3) and E3 text
T3 = {"COCO-4 (CPU host)": [(-13.3, -24.5, -2.1), (-18.0, -23.7, -12.3), (-9.4, -18.6, -0.2), (-28.1, -49.4, -6.8)],
      "COCO-4 (H100 host)": [(-5.9, -13.2, 1.5), (-13.4, -28.7, 1.9), (-6.1, -15.0, 2.7), (-34.4, -66.8, -1.9)],
      "COCO-6": [(-21.6, -30.8, -12.5), (-17.8, -29.6, -6.0), (-11.1, -20.1, -2.1), (-30.9, -56.7, -5.1)],
      "Flickr30k-4": [(-7.4, -10.6, -4.1), (-4.8, -9.3, -0.3), (-2.7, -5.5, 0.2), (-11.9, -20.8, -3.0)],
      "Synthetic-4": [(-23.1, -32.3, -13.9), (-16.5, -25.2, -7.7), (-15.9, -19.3, -12.6), (-32.3, -41.0, -23.7)]}
fir_vs_fulldet, wi_ratio, bd_ratio, cost_vs_cont, delays, false_rt, max_delay = [], [], [], [], [], 0, 0
for ds, src in SRC["e1"].items():
    E3 = load(src)["E3"]
    t = by(E3, "seed", "scenario", "policy")
    seeds = sorted({r["seed"] for r in E3})
    ds_delays = []
    label = "Synthetic-5 (printed) / Synthetic-4 (file)" if ds.startswith("Synth") else ds
    for i, sc in enumerate(SC):
        f = [t[(s, sc, "FIR+detector")] for s in seeds]
        st = [t[(s, sc, "Static")] for s in seeds]
        m, lo, hi, _ = paired([r["post_cost"] for r in f], [r["post_cost"] for r in st])
        c = T3[ds][i]
        add(f"Table III {label} {sc}", c[0], m, src, "E3.post_cost paired")
        add(f"Table III {label} {sc} CI low", c[1], lo, src, "t-interval")
        add(f"Table III {label} {sc} CI high", c[2], hi, src, "t-interval")
        fd = [t[(s, sc, "Full+detector")] for s in seeds]
        fe = [t[(s, sc, "Full every window")] for s in seeds]
        fir_vs_fulldet.append(paired([r["post_cost"] for r in f], [r["post_cost"] for r in fd])[0])
        cost_vs_cont.append(paired([r["post_cost"] for r in f], [r["post_cost"] for r in fe])[0])
        wi_ratio.append(np.mean([b["whatif"] for b in fe]) / np.mean([a["whatif"] for a in f]))
        bd_ratio.append(np.mean([b["builds"] for b in fe]) / max(np.mean([a["builds"] for a in f]), 1e-9))
        false_rt += sum(r["false_retunes"] for r in f)
        onset = 8 if sc == "recurring" else ONSET   # scenario() returns onset 8 for recurring
        ds_delays.append(np.mean([r["first_retune"] - onset for r in f]))
        max_delay = max(max_delay, max(r["first_retune"] - onset for r in f))
    delays.append(np.mean(ds_delays))
    detail.append(f"E3 {ds}: FIR+detector delay per seed/scenario = "
                  f"{[t[(s, sc, 'FIR+detector')]['first_retune'] for sc in SC for s in seeds]}")
add_range("VII-B gains new type 12-34%", 12, 34,
          [-T3[d][3][0] for d in T3], "Table III", "printed values", 0)
add("VII-B false re-tunes (all E3 FIR+detector runs)", 0, false_rt, "E3 files", "false_retunes sum", 0)
add_range("VII-B mean delay (windows), per dataset over 4 scenarios", 1.40, 1.45, delays, "E3 files",
          "first_retune - onset (onset 8 for recurring)", 2)
add("VII-B max delay (windows)", 4, max_delay, "E3 files", "max first_retune - onset", 0)
add_range("VII-C FIR vs Full+detector %", -2.3, 1.0, fir_vs_fulldet, "E3 files", "post_cost paired")
add_range("VII-C what-if ratio Full-every-window/FIR", 8, 27, wi_ratio, "E3 files", "whatif mean ratio", 0)
add("VII-C build ratio low end", 3.6, min(bd_ratio), "E3 files", "builds mean ratio", 1)
add("VII-C build ratio high end", 30, max(bd_ratio), "E3 files", "builds mean ratio", 0)
add_range("VII-C cost vs every-window %", -2, 6, cost_vs_cont, "E3 files", "post_cost paired", 0)

# ---------------------------------------------------------------- Table IV (E4), E4 text, E5
POL = [("Static", "Static"), ("Robust static", "Robust static"), ("FIR-MINT", "FIR+detector"),
       ("Full", "Full+detector"), ("Capped full", "Capped-full+det."), ("Cost trigger", "Cost-trigger+FIR"),
       ("Forecast", "Forecast+FIR"), ("Continuous", "Continuous FIR")]
T4 = {"Flickr30k-4": [(10.8, 12.9, .5, 1.2, 1.2, .5, .7, -.1), (8.1, 6.8, .6, 1.6, 1.9, .7, .6, -.1),
                      (11.5, 12.4, 3.5, 3.8, 3.8, 2.6, 5.2, 1.8), (21.0, 22.7, 2.2, 2.3, 2.3, 2.2, 2.8, 1.3)],
      "COCO-4": [(47.7, 19.3, 5.7, 6.0, 6.0, 10.5, 6.6, 3.5), (31.2, 34.5, 2.6, 2.6, 2.6, 5.4, 1.5, 1.1),
                 (40.5, 38.6, 7.9, 9.5, 9.5, 10.6, 19.5, 6.1), (59.5, 60.5, 6.8, 7.1, 7.1, 6.8, 8.3, 3.8)],
      "COCO-6": [(24.9, 30.2, .1, 2.8, 5.3, 2.7, 1.6, .2), (38.7, 30.5, 1.0, 2.4, 2.9, 3.5, 1.7, -.2),
                 (38.6, 31.5, 12.2, 12.4, 18.1, 12.9, 12.9, 6.2), (151.3, 132.1, 17.1, 16.2, 16.8, 20.3, 17.3, 8.7)]}
reg = {}
pre_reconf, wi4, bd4 = [], [], []
for ds, src in SRC["base"].items():
    E4 = load(src)["E4"]
    t = by(E4, "seed", "scenario", "policy")
    seeds = sorted({r["seed"] for r in E4})
    for i, sc in enumerate(SC):
        orc = [t[(s, sc, "Oracle")]["post_cost"] for s in seeds]
        for j, (lab, key) in enumerate(POL):
            r = (np.mean([t[(s, sc, key)]["post_cost"] / o - 1 for s, o in zip(seeds, orc)]) * 100)
            reg[(ds, sc, lab)] = r
            if ds in T4:
                add(f"Table IV {ds} {sc} {lab}", T4[ds][i][j], r, src, "post_cost/Oracle-1 mean")
        c = [t[(s, sc, "Continuous FIR")] for s in seeds]
        f = [t[(s, sc, "FIR+detector")] for s in seeds]
        if ds in T4:
            pre_reconf.append(np.mean([x["false_retunes"] for x in c]))  # re-tunes before onset
            wi4.append(np.mean([x["whatif"] for x in c]) / np.mean([x["whatif"] for x in f]))
            bd4.append(np.mean([x["builds"] for x in c]) / max(np.mean([x["builds"] for x in f]), 1e-9))
real = [d for d in T4]
add_range("Table IV caption: Continuous reconfigurations before drift", 5.6, 9.2, pre_reconf,
          "baselines files", "Continuous FIR false_retunes mean", 1)
add_range("Table IV caption / abstract: what-if ratio Continuous/FIR", 8, 29, wi4, "baselines files", "whatif ratio", 0)
add_range("Table IV caption: build ratio Continuous/FIR", 3, 20, bd4, "baselines files", "builds ratio", 0)
add_range("VII-D robust static above hindsight %", 7, 132,
          [reg[(d, s, "Robust static")] for d in real for s in SC], "baselines files", "regret", 0)
within8 = sum(reg[(d, s, "FIR-MINT")] <= 8 for d in SRC["base"] for s in SC)
add("VII-D FIR within 8% of hindsight (of 16 pairs)", 14, within8, "baselines files", "count", 0)
diff_cont = [reg[(d, s, "FIR-MINT")] - reg[(d, s, "Continuous")] for d in real for s in SC]
add_range("VII-D Continuous buys points", 1, 9, diff_cont, "baselines files", "FIR - Continuous regret", 0)
le_full = sum(round(reg[(d, s, "FIR-MINT")], 1) <= round(reg[(d, s, "Full")], 1) for d in SRC["base"] for s in SC)
add("VII-D FIR <= Full (of 16 pairs)", 13, le_full, "baselines files", "count", 0)
add("VII-D FIR worse than Full by at most (points)", 0.9,
    max(reg[(d, s, "FIR-MINT")] - reg[(d, s, "Full")] for d in SRC["base"] for s in SC),
    "baselines files", "max FIR - Full")
add("VII-D cost trigger worse on COCO-4 by up to (points)", 4.8,
    max(reg[("COCO-4", s, "Cost trigger")] - reg[("COCO-4", s, "FIR-MINT")] for s in SC), "baselines coco4", "max")
E4c4 = load(SRC["base"]["COCO-4"])["E4"]
for key, lo, hi, lab in (("Cost-trigger+FIR", 20, 44, "cost trigger"), ("FIR+detector", 49, 158, "FIR")):
    v = [np.mean([r["whatif"] for r in E4c4 if r["policy"] == key and r["scenario"] == s]) for s in SC]
    add_range(f"VII-D COCO-4 what-if calls {lab}", lo, hi, v, SRC["base"]["COCO-4"], "whatif mean per scenario", 0)

E5txt = {"Synthetic": (2.8, 3.5), "Flickr30k-4": (1.7, 2.1), "COCO-4": (6.3, 7.6), "COCO-6": (7.2, 8.7)}
for ds, src in SRC["base"].items():
    E5 = load(src)["E5"]
    settings = sorted({(r["window"], r["k_sigma"]) for r in E5})
    regs = [np.mean([r["regret"] for r in E5 if (r["window"], r["k_sigma"]) == st]) * 100 for st in settings]
    add_range(f"VII-E regret range over 9 settings {ds}", *E5txt[ds], regs, src, "E5.regret mean per setting")
    fr = max(np.mean([r["false_retunes"] for r in E5 if (r["window"], r["k_sigma"]) == st]) for st in settings)
    add(f"VII-E max false re-tunes per run {ds}", None, fr, src, "E5.false_retunes", 2)
    fr300 = sum(r["false_retunes"] for r in E5 if r["window"] >= 300 and r["k_sigma"] == 3.0)
    add(f"VII-E false re-tunes at >=300 queries, 3 sigma {ds}", 0, fr300, src, "sum", 0)

# ---------------------------------------------------------------- Table V and total time (E6)
T5 = {"Flickr30k-4": [(.8, .7), (.5, .2), (3.3, 2.0), (2.0, 1.1)],
      "COCO-4": [(5.8, 4.3), (2.7, 1.6), (7.9, 4.7), (6.4, 3.8)],
      "COCO-6": [(-1.4, -3.0), (2.1, 1.2), (11.6, 7.3), (16.3, 9.8)],
      "Synthetic-5": [(2.2, 1.4), (.9, .8), (5.9, 3.2), (6.2, 3.6)]}
fast_red = []
for ds, src in SRC["ext"].items():
    d = load(src)
    E6 = d["E6"]
    seeds = sorted({r["seed"] for r in E6})
    one = {(r["seed"], r["scenario"], r["policy"]): r for r in E6 if r["qw"] is None}
    for i, sc in enumerate(SC):
        orc = [one[(s, sc, "Oracle")]["post_cost"] for s in seeds]
        r0 = np.mean([one[(s, sc, "FIR+detector")]["post_cost"] / o - 1 for s, o in zip(seeds, orc)]) * 100
        r1 = np.mean([one[(s, sc, "FIR+fast")]["post_cost"] / o - 1 for s, o in zip(seeds, orc)]) * 100
        add(f"Table V {ds} {sc} default", T5[ds][i][0], r0, src, "post_cost/Oracle-1")
        add(f"Table V {ds} {sc} fast path", T5[ds][i][1], r1, src, "post_cost/Oracle-1")
        if ds != "Synthetic-5":
            fast_red.append((T5[ds][i][0] - T5[ds][i][1]) / T5[ds][i][0] * 100 if T5[ds][i][0] > 0 else np.nan)
    ff = sum(r["false_retunes"] for r in E6 if r["policy"] == "FIR+fast")
    add(f"VII-F fast path false re-tunes {ds}", 0, ff, src, "sum", 0)
    fs = d.get("fast_sweep", [])
    if fs:
        add(f"VII-F fast sweep false re-tunes {ds}", 0, sum(r["false_retunes"] for r in fs), src, "fast_sweep sum", 0)
add("VII-G fast path reduces regret by up to 40% (real data), recomputed from Table V", 40, float(np.nanmax(fast_red)),
    "Table V printed", "max relative reduction", 0)

# total time: per policy and Qw, relative to FIR+detector, per seed then mean
tt = {}
for ds, src in SRC["ext"].items():
    E6 = load(src)["E6"]
    seeds = sorted({r["seed"] for r in E6})
    for sc in SC:
        base = {r["seed"]: r["total_s"] for r in E6 if r["scenario"] == sc and r["policy"] == "FIR+detector"}
        for pol in ("Static", "FIR+fast", "FIR+SR", "FIR+fast+SR", "Full+detector", "Continuous FIR"):
            for q in ("1000", "10000", "100000"):
                R = [r for r in E6 if r["scenario"] == sc and r["policy"] == pol
                     and (r["qw"] is None or str(r["qw"]) == q)]
                if not R:
                    continue
                tt[(ds, sc, pol, q)] = np.mean([r["total_s"][q] / base[r["seed"]][q] - 1 for r in R]) * 100
avg = lambda ds, pol, q: np.mean([tt[(ds, sc, pol, q)] for sc in SC])
add("VII-F Flickr Qw=1000 Static vs FIR mean %", -16, avg("Flickr30k-4", "Static", "1000"), "ext flickr4", "total_s", 0)
add("VII-F Flickr Qw=1000 Static vs FIR recurring %", -37, tt[("Flickr30k-4", "recurring", "Static", "1000")],
    "ext flickr4", "total_s", 0)
add("VII-F Flickr Qw=1000 FIR+SR vs FIR mean %", -15.2, avg("Flickr30k-4", "FIR+SR", "1000"), "ext flickr4", "total_s")
for pol in ("FIR+SR", "FIR+fast+SR"):
    add(f"VII-F COCO-6 recurring Qw=1000 {pol} saving %", None, tt[("COCO-6", "recurring", pol, "1000")],
        "ext coco6", "total_s", 1, "printed: saves 14-16%")
REAL = [d for d in SRC["ext"] if not d.startswith("Synth")]
add("VII-F waiting costs at most X% (FIR+SR, Qw=1000, real)", 5.6,
    max(tt[(d, s, "FIR+SR", "1000")] for d in REAL for s in SC), "ext files", "total_s", 1)
hi_diff = [abs(tt[(d, s, "FIR+SR", "100000")]) for d in REAL for s in SC]
add("VII-F high traffic SR vs immediate, max |diff| %", 0.2, max(hi_diff), "ext files", "total_s", 1)
st_hi = [tt[(d, s, "Static", "100000")] for d in REAL for s in SC]
add("VII-F Static up to X% more at high traffic", 67, max(st_hi), "ext files", "total_s", 0)
QS = ("1000", "10000", "100000")
worst_fsr = max(tt[(d, s, "FIR+fast+SR", q)] for d in REAL for s in SC for q in QS)
add("VII-F FIR+fast+SR never worse than default by more than % (real)", 3.8, worst_fsr, "ext files", "total_s")
add("VII-F same, synthetic (claim says every dataset)", None,
    max(tt[("Synthetic-5", s, "FIR+fast+SR", q)] for s in SC for q in QS), "ext synthetic", "total_s", 1,
    "exceeds 3.8; claim holds on real data only")
gap, gap_syn = [], []
for d in SRC["ext"]:
    for q in ("1000", "10000", "100000"):
        means = {p: avg(d, p, q) for p in ("Static", "FIR+fast", "FIR+SR", "FIR+fast+SR")}
        means["FIR+detector"] = 0.0
        (gap_syn if d.startswith("Synth") else gap).append(means["FIR+fast+SR"] - min(means.values()))
add("VII-F FIR+fast+SR within X points of best mean (real)", 1.1, max(gap), "ext files", "total_s, best of 5 policies")
add("VII-F same, synthetic", None, max(gap_syn), "ext synthetic", "total_s", 1, "exceeds 1.1; claim holds on real data only")

# ---------------------------------------------------------------- E2 synthetic text and Fig. 5
abl = load(SRC["abl"])
def abl_stat(C, setting):
    R = [r for r in abl if r["C"] == C and r["setting"] == setting]
    if not R:
        return None, None
    save = np.mean([r["full_calls"] / r["calls"] for r in R])
    closed = np.mean([(r["static_ratio"] - r["cost_ratio"]) / (r["static_ratio"] - 1) for r in R]) * 100
    return save, closed
settings = sorted({r["setting"] for r in abl}); Cs = sorted({r["C"] for r in abl})
detail.append(f"Ablation settings {settings}, C values {Cs}")
for C in Cs:
    for st in settings:
        s, c = abl_stat(C, st)
        detail.append(f"  ablation C={C} {st}: saving {s:.2f}x, gap closed {c:.1f}%")
# ---------------------------------------------------------------- method text: pilot timing
pil = load(SRC["pilot"])
detail.append("pilot.json keys: " + str(list(pil)[:10]))

# ---------------------------------------------------------------- abstract, intro, method text
add_range("Abstract: post-drift cost reduced by 3-34% (from Table III)", 3, 34,
          [abs(v[0]) for d in T3 for v in T3[d]], "Table III printed", "range of |mean|", 0)
c6 = load(SRC["base"]["COCO-6"])["E4"]
st = {r["seed"]: r["post_cost"] for r in c6 if r["scenario"] == "new_type" and r["policy"] == "Static"}
oc = {r["seed"]: r["post_cost"] for r in c6 if r["scenario"] == "new_type" and r["policy"] == "Oracle"}
ratios = [st[s] / oc[s] for s in st]
add("Intro: static up to 2.5x more expensive (COCO-6 new type, Static/Oracle mean)", 2.5, float(np.mean(ratios)),
    SRC["base"]["COCO-6"], "mean over seeds of Static/Oracle", 1,
    f"a mean over 5 seeds, not a maximum; per-seed max {max(ratios):.2f}x")
s12, g12 = abl_stat(12, "Adaptive (3..8, 80%)")
add("VII-C 12 columns what-if saving (x)", 3.1, s12, SRC["abl"], "full_calls/calls mean")
add("VII-C 12 columns gap closed (%)", 96, g12, SRC["abl"], "(static-cost)/(static-1)", 0)
s3, g3 = abl_stat(12, "K=3"); s12k, g12k = abl_stat(12, "K=12")
add("VII-C K=3 saving (x)", 9.4, s3, SRC["abl"], "C=12"); add("VII-C K=3 gap (%)", 65, g3, SRC["abl"], "C=12", 0)
add("VII-C K=12 saving (x)", 2.1, s12k, SRC["abl"], "C=12"); add("VII-C K=12 gap (%)", 100, g12k, SRC["abl"], "C=12", 0)
pil = load(SRC["pilot"])
detail.append("Method text 'build 4-12 s, re-tune about 1 ms (Flickr30k, 3 seeds)' -> runs/pilot_mint_flickr/pilot.md: "
              "build 3.95-12.43 s, what-if wall 0.75-1.62 ms. Matches.")
# review item 10: Table III (E3 run) vs Table IV (E4 run), COCO-6 new type
c6e3 = load(SRC["e1"]["COCO-6"])["E3"]
f4 = [r["post_cost"] for r in sorted(c6, key=lambda r: r["seed"]) if r["scenario"] == "new_type" and r["policy"] == "FIR+detector"]
s4 = [r["post_cost"] for r in sorted(c6, key=lambda r: r["seed"]) if r["scenario"] == "new_type" and r["policy"] == "Static"]
add("Review #10: COCO-6 new type FIR vs Static, paired, in the E4 run", None, paired(f4, s4)[0], SRC["base"]["COCO-6"],
    "post_cost paired", 1, "Table III prints -30.9 from the E3 run; the two runs are calibrated separately")

# ---------------------------------------------------------------- write
out = ROOT / "stage1"
with open(out / "trace_table.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader(); w.writerows(rows)
n = {k: sum(r["status"] == k for r in rows) for k in ("match", "MISMATCH", "info", "not traced")}
L = ["# Stage 1 trace of draft v1.0", "", f"Rows: {len(rows)}; " + ", ".join(f"{k}: {v}" for k, v in n.items()), "",
     "| Place | Printed | Recomputed | Status | Source | Note |", "|---|---:|---:|---|---|---|"]
for r in rows:
    L.append(f"| {r['place']} | {r['printed']} | {r['recomputed']} | {r['status']} | `{r['source']}` | {r['note']} |")
L += ["", "## Detail", ""] + [f"- {x}" for x in detail]
(out / "trace_report.md").write_text("\n".join(L), encoding="utf-8")
print("\n".join(L[:3]))
for r in rows:
    if r["status"] != "match":
        print(r["status"], "|", r["place"], "| printed", r["printed"], "| recomputed", r["recomputed"], "|", r["note"])
