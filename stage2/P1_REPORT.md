# Pilot P1 (scale): result

Date: 2026-11-08. Run: PBS job 466054 on hpc3-c02-n05 (Xeon E5-2680 v4, exclusive node),
commit f0a3b16, frozen `fir_mint_v4.py` sha256 a1fe7001..., 28 build threads, single-threaded
search. Wall time 1 h 02 min, peak RSS 76.0 GB. Label: **measured**.
Result file: `results/p1/laion_1m_4col/p1.json` (per-query recall: `recall_by_query.csv`).

Table: LAION-400M shards 0-1, 1,000,000 rows x 4 columns (512-d), 2,000 held-out queries
(see `embeddings/laion_1m_4col/meta.json` and WORK_PLAN.md, "Deviations"). The second table
of the brief (MINT News) is not run: its licence is open.

## Pass condition (fixed 2026-11-08)

"A measured gain over Static: the paired per-seed differences all in the same direction (sign
test) and a bootstrap interval, marked indicative with 5 seeds, that excludes zero."

| Comparison | Per-seed change (%) | Mean | Bootstrap 95% CI (indicative) | Seeds lower | Sign test p |
|---|---|---:|---|---:|---:|
| FIR-MINT vs Static | -44.84, -0.64, +0.06, -25.42, -0.07 | -14.18 | [-32.00, -0.13] | 4 of 5 | 0.375 |
| Full re-tune vs Static | -44.81, -1.12, +0.60, -25.46, -0.08 | -14.17 | [-31.86, -0.02] | 4 of 5 | 0.375 |
| FIR-MINT vs Full re-tune | -0.05, +0.48, -0.53, +0.05, 0.00 | -0.01 | [-0.32, +0.28] | 2 of 5 | 1.0 |

**P1 as written: FAIL.** The interval excludes zero, but the directions are not all the same:
on seed 2 FIR-MINT is +0.06% slower than Static.

What lies behind the failure (for the authors' decision, not a change of the condition):
- On seeds 2 and 4 FIR-MINT kept Static's configuration unchanged. The +0.06% and -0.07% are
  timing noise between two runs of the same configuration.
- On the three seeds where FIR-MINT changed the configuration, it was faster each time
  (-44.8%, -0.6%, -25.4%). The gain is concentrated in two seeds.
- With 5 seeds a sign test cannot reach p < 0.05 unless all 5 agree (minimum p = 0.0625).

## Other P1 measurements

Build time and memory per index (1M rows, HNSW M=32, efConstruction=128, 28 threads):

| Index width | Build time (s) | Raw vectors (GB) | Graph (GB) |
|---|---|---:|---:|
| 1 column (512-d) | 105-130 | 2.05 | 0.27 |
| 2 columns (1024-d) | 189-248 | 4.10 | 0.27 |
| 3 columns (1536-d) | 291-343 | 6.14 | 0.27 |

In the draft, builds took 4-12 s at 30k rows. A re-tune that adds two indexes now costs
224-465 s of builds (8 threads would take longer). One window at Q_w = 10,000 and about 9 ms
per query serves in about 90 s, so one build costs several windows of query time: RQ3 matters
at this scale.

Flat scan (exact, single thread, 1M rows): 171-173 ms for one column, 337-340 ms for two,
503-505 ms for three. The cheapest plans of FIR-MINT's configurations take 1.3-1.5 ms
(single column) and 7.0-16.9 ms (multi-column) per query type (median over seeds). Flat scan
is 20x to 130x slower; it is not a competitive plan at 1M rows.

Estimator calibration (v1.0, includes building all 14 indexes on seed 0): 3,110 s on seed 0,
12-29 s on later seeds (indexes cached).

## Recall (brief M4, input for P4 and C3)

| Seed | Policy | v1.0 measure (min over types of type-mean recall) | Violating mass (v1.0) | Share of queries below 0.90 |
|---|---|---:|---:|---:|
| 3 | all three | 0.957 | 0 | 0.020 |
| 4 | Full re-tune | **0.892** | **0.0338** | 0.015 |
| 4 | Static, FIR-MINT | 0.978 | 0 | 0.010 |
| 0-2 | all | 0.970-0.988 | 0 | 0.002-0.008 |

- Full re-tune on seed 4 adopted a configuration whose estimated recall met the target and whose
  measured recall does not (3.4% of the workload in violation), at a cost of 462 s of builds and
  no latency gain. The v1.0 estimator's recall guarantee fails at 1M rows.
- Per-query recall falls below 0.90 for 0.2% to 2.0% of queries for every policy, while the
  per-type means stay above 0.90. The proposed C3 allowance is 1%.
- Full re-tune on seed 2 built 2 indexes (465 s) and was 0.6% slower than Static: the estimated
  gain did not appear in the measurement (M2).

## What the authors need to decide

1. P1 failed as written. The brief's rule: "The current claims do not hold at scale. Re-scope,
   or choose another venue." The mean gain (-14.2%) is close to the draft's 13-19% at 30k rows,
   but it comes from 2 of 5 seeds; on 2 seeds no re-tune was needed.
2. The second P1 table (MINT News) is blocked on its licence.
3. Whether to continue with P3, P2a, P4 and P2b while P1 is discussed. They are independent of
   P1's outcome and P4 already has evidence from this run.
