# P3 protocol: tuner cost and faithfulness, fixed before any P3 run

Recorded 2026-11-08. Pass conditions are the brief's (Part 6.8, margins confirmed by the
collaborator and by Rao, Reply 1 A5). This file only defines how they are measured, where the
brief leaves it open. Tuner: C4 (`stage2/p3/C4_DESIGN.md`).

## Terms

- **Calibration**: one-time per table. Fitting the numDist and recall models on the single-column
  indexes, and the exact scores of the training query sample. Building the single-column indexes is
  **build time**, reported separately (Reply 1, R1).
- **Tuning**: Algorithm 2 (beam search) with the planner, for one workload.
- **Cold re-tune**: a new tuner object: calibration + tuning, empty plan caches.
- **Warm re-tune**: the tuner that tuned the previous workload: no calibration, plan caches kept,
  beam seeded with the current configuration.

## Pass condition 1: faithfulness (factor 3)

MINT reports index tuning time (Fig. 14, excluding one-time training) of about 85 to 185 s for 10 to
16 queries on 1M rows (brief Part 4.2, read from the plot). C4 runs MINT's workload construction on
LAION-1M-4: each query selects every column independently with p = 0.5 (non-empty), distinct
queries, weights Uniform(0,1) normalised, recall@100, theta = 0.90, beam width 5, di = 2, se = 2,
im = 5%. With 4 columns there are 15 possible queries, so sizes 10, 12 and 14 are run (5 seeds
each). **Pass**: the median C4 tuning time at every size lies within [85 / 3, 185 x 3] = [28.3, 555]
seconds. Caveats stated with the result: different data (LAION-1M-4 vs MINT's semi-synthetic 8
columns), different hardware, a range read from a plot. Calibration time is reported beside it
(MINT Fig. 12 reports training separately: 3 to 32 s).

## Pass condition 2: warm start (at least 30%)

On the draft's workload construction (stable Zipf workload, then the abrupt drift, 14 query types,
k = 10, theta = 0.90, budget 8 extra units), seeds 0 to 4. Per seed: cold re-tune on the drifted
workload versus warm re-tune on the same drifted workload after tuning the stable one.
**Primary (judged)**: tuning time only, warm versus cold; the cut must be at least 30% (median over
seeds, and reported per seed). This is the stricter reading: counting calibration in the cold time
would make the cut large by construction, because a warm re-tune never recalibrates.
**Also reported**: the cut including calibration in the cold time.

## Reported, not gated

- Ratio of tuner time to one window's service time (Static configuration, stable workload,
  Q_w = 10,000, measured latency on the same table), as the brief says.
- Beam width sweep b in {3, 5, 10}: tuning time and estimated cost.
- What-if calls (planner calls that miss the cache) as a secondary count.
- Build time of the single-column indexes and of each adopted index (wall clock, 28 threads, and
  CPU-seconds).
- Agreement of C4's choice with v1.0's greedy tuner on the same workloads (configuration and
  estimated cost).

## Settings

Exclusive Xeon E5-2680 v4 node, 28 threads for builds and for calibration's matrix products,
single thread for search and for the planner. Five repetitions of timing per measurement where
the brief asks for them (tuner time: 5 seeds x 1 timing; repeated timing of the same seed is
reported once for seed 0 with 5 repetitions). Label: measured.
