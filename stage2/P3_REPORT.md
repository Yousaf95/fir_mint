# Pilot P3 (tuner cost): result

Date: 2026-11-08. Tuner: C4, a re-implementation of MINT's tuner from its paper
(`stage2/p3/mint_c4.py`, design and deviations `stage2/p3/C4_DESIGN.md`). Protocol fixed before
the run: `stage2/p3/P3_PROTOCOL.md`. Label: **measured** (wall clock on exclusive Xeon E5-2680 v4
nodes, 28 build threads, single-threaded planner and search).

Runs: LAION-1M-4, PBS job 467139, code 66a170b (see `stage2/PROVENANCE_CORRECTIONS.md`),
`results/p3/laion_1m_4col/p3.json`. Timing only on the P2a tables (COCO-4, COCO-6, Flickr30k-4 at
30k rows): job 467151, code 92e6abd, `results/p3/*/p3_timing.json`. COCO-6 at full size (117,266
rows, Reply 1 D2): job 467493, code 800b83b, `results/p3/coco_full_6col/p3_timing.json`. Per-seed
tables: `stage2/STATUS_REPORT2_TABLES.md`.

## Pass conditions

| Condition | Measured | Result |
|---|---|---|
| Faithfulness: median C4 tuning time on MINT's workload construction within [85/3, 185 x 3] = [28.3, 555] s at every size | 10 queries 33.9 s; 12 queries 33.4 s; 14 queries 37.5 s (5 seeds each; LAION-1M-4, recall@100, budget 4 indexes) | **PASS** |
| Warm start cuts cold tuning time by at least 30% (tuning only, median over seeds) | 91.5% on LAION-1M-4 (per seed 87.6, 82.9, 100.0, 95.8, 91.5%) | **PASS** |

Warm start on the other tables (reported): COCO-6 full 93.8%, COCO-4 30k 100.0%, COCO-6 30k 93.2%,
Flickr30k-4 30k 89.6%. Including calibration in the cold time, the cut is 98.2-100% on LAION-1M-4.

Caveats on faithfulness: different data (LAION-1M-4, 4 columns, so at most 15 distinct queries)
and hardware than MINT's Fig. 14 (semi-synthetic 8 columns, AMD EPYC 7763); MINT's range is read
from a plot. On 7 of the 15 MINT-construction workloads (all 5 at 14 queries, 1 at 10, 1 at 12)
no configuration met recall@100 within 4 indexes; C4 returned the least-violating configuration
after the full search, so the timing is valid but the tuner found no feasible answer.

## Tuner cost

| Table | Calibration (s) | Cold tuning, median (s) | Warm re-tune, median (s) | Planner calls cold / warm (LAION) |
|---|---:|---:|---:|---|
| LAION-1M-4 (1M rows) | 118.1 (fits 26.6, scores 0.5, ranks 91.0) | 13.61 (5 repeats of seed 0: 14.05-14.07) | 1.15 | 300-308 / 0-32 |
| COCO-6 full (117k rows) | 33.9 (fits 14.9, ranks 18.9) | 56.06 (5 repeats of seed 0: 55.26-55.32) | 3.46 | 1264-1288 / 0-72 |
| COCO-4 (30k) | 8.9 | 12.00 | 0.005 | |
| COCO-6 (30k) | 15.8 | 49.05 | 3.264 | |
| Flickr30k-4 (28k) | 10.4 | 12.71 | 1.320 | |

Calibration grows with the rows (exact full-table ranks for the query sample, a documented
deviation from MINT's 1% data sample); tuning does not (the planner works on the ranks).
MINT reports 3-32 s for its one-time training.

Beam width on LAION-1M-4 (seed 0, drifted workload): b = 3: 13.46 s; b = 5: 14.08 s; b = 10:
15.22 s; the same configuration and estimated cost in all three. COCO-6 full: 54.66, 55.42, 58.68 s;
same configuration and cost.

Builds (wall clock, 28 threads; CPU-seconds in brackets): single-column indexes at 1M rows 76-91 s
(1,873-2,243); the three 2-column indexes adopted 176-225 s (4,306-5,503). At 117k rows (COCO-6 full),
3.0-6.4 s (73-154). At 30k rows, 0.4-0.5 s.

Tuner time against window time (LAION-1M-4, C4's Static configuration on the stable workload,
measured latency 0.80 ms, so a window at Q_w = 10,000 serves in 8.0 s): a cold re-tune including
calibration costs 16.6 windows, a warm re-tune 0.22 windows.

## Findings for the paper and the next pilots

1. **A faithful tuner is not free, and warm start matters.** Cold tuning takes 12-49 s on the
   draft's tables (the draft assumed about 1 ms) and calibration 9-118 s; warm re-tuning removes
   83-100% of the tuning time because the planner's cache survives across windows. The detector's
   value now depends on this cost (P2a).
2. **C4's recall estimate fails at 1M rows on correlated columns.** Measured on 600 held-out
   queries, C4's Static configuration has minimum type-mean recall 0.70 and 8.2% of queries below
   0.90, although C4 estimated every type feasible. Estimated against measured, per type: captions
   only (1,2,3) 0.907 against **0.700**; image + two captions (0,1,3) 0.908 against **0.860**; the
   other 12 types are met or exceeded (0.913 to 1.000 measured). Both failing types combine the
   three caption columns that derive from the same caption. Hypothesis for P4: C4 treats misses in
   different indexes as independent; correlated columns break that.
3. **On LAION-1M-4 the configuration does not move.** C4 chose the same configuration (single
   columns plus the three image-caption pairs) on all 5 seeds, for the stable and the drifted
   workload, and for beam widths 3, 5, 10. Under MINT's cost model the drift does not change the
   best configuration on this table, so re-tuning has nothing to gain here. This differs from
   v1.0's tuner in P1, which changed the configuration on 3 of 5 seeds. To be examined before P1b
   (cost model, budget, or data). Hypothesis linking findings 2 and 3: C4 believes that query
   types over the three correlated caption columns reach 0.90 cheaply by merging single-column
   searches (it estimates 0.907 for captions-only, measured 0.700), so it never spends budget on
   text indexes, whatever the drift; with a correct recall estimate a text-heavy drift would need
   text indexes and the configuration would move. P4 tests both together.
4. **MINT's single cost line is a poor fit at small ek.** On LAION-1M-4 it overestimates the
   measured distance count at ek = 100 by 28-39%; on Flickr30k (28k rows) by 69-78%. C4 uses
   piecewise-linear interpolation (deviation, documented).
5. **The configuration moves on the six-column tables.** C4's drifted-workload configuration
   differs from the stable one on all 5 seeds of COCO-6 full and on 4 of 5 of COCO-6 30k, against
   0 of 5 on LAION-1M-4 and COCO-4 30k and 3 of 5 on Flickr30k-4. Finding 3 is therefore specific to
   the 4-column tables (few distinct query types), not to C4. COCO-6 full is the table on which
   re-tuning has something to gain under MINT's cost model.
6. **Warm start sometimes finds a cheaper configuration than cold tuning.** On Flickr30k-4 warm
   re-tuning ends 0.24-0.51% cheaper than cold tuning on all 5 seeds, and on COCO-6 full on 2 of 5
   seeds (-0.48%, -0.53%): Algorithm 2's beam search is a local search, and the start point
   matters. Warm was never more expensive than cold by more than 0.03%.

## Deviations from MINT (all decided before the run, `C4_DESIGN.md`)

Exact full-table ranks for a query sample instead of a 1% data sample; cost and recall models
fitted on the full single-column indexes; piecewise-linear numDist; monotone planner for
|X_q| > 3; storage as the sum of index widths with single-column indexes fixed (draft setting) or
MINT's count of indexes (faithfulness check); search proceeds through infeasible configurations
and returns the cheapest feasible one seen. In the P3 runner all single-column indexes are HNSW,
including COCO's duplicate-heavy category column (v1.0 uses a flat index there); this affects build
and calibration time on the 30k COCO tables only.
