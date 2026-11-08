# Pilot P2a (is the detector needed?): result

Date: 2026-11-08. Protocol fixed before the run: `stage2/p2a/P2a_PROTOCOL.md`. Runner
`stage2/p2a/p2a_run.py` (frozen v1.0 simulator imported unchanged), analysis
`stage2/p2a/p2a_analyze.py`, summary `results/p2a/p2a_summary.json`, per-seed tables
`stage2/STATUS_REPORT2_TABLES.md`. Label: **estimated** query time (frozen calibrated estimator);
the build model and the tuner cost per invocation are measured inputs (tuner cost: C4, P3).

Runs: 30 seeds (0-29) per table. COCO-4, COCO-6, Flickr30k-4 at 30k rows: jobs 467162-467164, code
ca8085c. COCO-6 full (117,266 rows): job 467494, code 800b83b. FIR+fast+SR equals the frozen E6
code on seeds 0 and 1 on every table (24 of 24 rows equal per table).

## Pass condition and result

Per table, under the C4 warm re-tune cost, at every Q_w in {1,000; 10,000; 100,000}: mean over
30 seeds of d = FIR+fast+SR total / Continuous+SR total - 1 at most -5%, and the upper end of the
bootstrap 95% interval below 0.

| Table | Warm tuner cost (s) | d @ Q_w = 1,000 | d @ 10,000 | d @ 100,000 | Result |
|---|---:|---|---|---|---|
| COCO-4 30k | 0.005 | -2.27% [-3.81, -0.96] | -0.34% [-0.70, -0.00] | +0.16% [-0.13, +0.50] | **FAIL** |
| COCO-6 30k | 3.264 | **-44.50%** [-47.34, -41.80] | **-8.98%** [-10.30, -7.76] | -1.25% [-1.61, -0.90] | **FAIL** |
| Flickr30k-4 28k | 1.320 | **-40.89%** [-41.17, -40.55] | **-7.43%** [-7.73, -7.13] | -0.65% [-0.71, -0.58] | **FAIL** |
| COCO-6 full 117k | 3.463 | **-14.73%** [-15.89, -13.62] | -1.57% [-1.80, -1.33] | -0.24% [-0.51, +0.05] | **FAIL** |

Bold: meets the condition at that Q_w. **P2a fails as written on all four tables.** The detector is
never worse by more than 0.16% (COCO-4, Q_w = 100,000, interval includes 0), and wins by 5% or more
only at low traffic on the tables where a warm re-tune costs seconds.

Other tuner costs (reported, not gated):

| Table | 1 ms (the draft's figure) | C4 cold tuning |
|---|---|---|
| COCO-4 30k | -2.13 / -0.32 / +0.16% | -73.70 / -29.11 / -4.22% |
| COCO-6 30k | -3.47 / -0.18 / -0.25% | -86.78 / -55.40 / -13.06% |
| Flickr30k-4 28k | -0.14 / -0.59 / +0.12% | -82.35 / -40.81 / -6.79% |
| COCO-6 full 117k | -3.64 / -0.07 / -0.08% | -66.05 / -19.60 / -2.53% |

(values at Q_w = 1,000 / 10,000 / 100,000.)

## Context (mean per run of one scenario)

| Table | Q_w | Firings FIR | Switches FIR / Cont | False switches FIR / Cont | Builds FIR / Cont |
|---|---:|---:|---|---|---|
| COCO-4 30k | 100,000 | 1.98 | 1.65 / 7.80 | 0.03 / 2.35 | 2.77 / 9.58 |
| COCO-6 30k | 100,000 | 1.84 | 1.75 / 13.33 | 0.01 / 4.24 | 3.96 / 19.66 |
| Flickr30k-4 28k | 100,000 | 1.98 | 1.52 / 1.52 | 0.00 / 0.15 | 2.83 / 2.45 |
| COCO-6 full 117k | 100,000 | 1.84 | 1.75 / 18.17 | 0.01 / 5.72 | 3.79 / 26.62 |

At Q_w = 1,000 and 10,000 both policies switch rarely (Continuous+SR 0.01-1.27 switches per run).
Continuous+SR re-tunes 30 times per run.

## Findings

1. **The detector's gain is tuner time saved.** With the draft's 1 ms tuner cost, FIR+fast+SR and
   Continuous+SR differ by at most 3.6% (and by less than 0.6% at Q_w >= 10,000): without a tuner
   cost, re-tuning every window under the same ski-rental rule is as good in total time. The gap opens only
   when each re-tune costs seconds (C4 warm, 1.3-3.5 s on three tables) and the window is short
   (low Q_w). On COCO-4 a warm re-tune costs 5 ms (the configuration does not move, P3) and the
   detector gains nothing.
2. **The detector keeps the system stable at high traffic.** At Q_w = 100,000, Continuous+SR
   switches 7.8-18.2 times per run on the COCO tables, with 2.4-5.7 false switches (before the
   drift onset), against at most 1.75 switches and 0.03 false switches for FIR+fast+SR, at equal total
   time (within 1.3%). Total time does not penalise this churn in the simulator. Whether it should
   (build interference with serving, memory peaks) is a question for the paper's cost model.
3. **The gain shrinks with table size at fixed tuner cost.** COCO-6 at 30k and at 117k have nearly
   the same warm tuner cost (3.26 vs 3.46 s), but the gain at Q_w = 1,000 falls from -44.5% to
   -14.7% because a window's query time grows with the rows. At 1M rows (LAION-1M-4, warm re-tune
   1.15 s, window at Q_w = 10,000 about 8 s measured) the tuner term would be smaller still relative
   to query time.
4. **Recall-violating mass is not zero beyond seed 4.** It is positive on 4 of 30 seeds on COCO-4
   (8, 9, 16, 22) and COCO-6 30k (5, 8, 16, 17), 2 of 30 on Flickr30k-4 (8, 27) and on COCO-6 full
   (12, 20), equally for every policy including Static: on those seeds the frozen estimator finds
   some query type infeasible for every configuration. The draft's "zero violating mass" holds for
   its seeds 0-4 only. Input for P4.

## Readings to confirm (stated in the protocol before the run)

(a) The gated tuner cost is the warm re-tune time. (b) The condition must hold at every Q_w. (c)
Continuous+SR keeps the rent account while its proposal stays the same. Under (b) read as "on
average over Q_w", COCO-6 30k and Flickr30k-4 would pass and COCO-4 and COCO-6 full would still
fail; this is reported, not used.

## What the authors need to decide

P2a fails as written. The result supports a narrower claim than C2 in v1.0: the detector saves
tuner invocations and avoids churn; it does not lower total time when tuning is cheap or traffic
is high. Options: keep C2 and state the regime (tuner cost per re-tune comparable to window query
time); re-frame C2 around stability (switches and false switches) with a cost model that charges
builds against serving; or drop the detector claim and present FIR-MINT as warm-start plus
ski-rental. P2b and P4 do not depend on this choice and can run first.
