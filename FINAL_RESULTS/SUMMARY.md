# FIR-MINT Final Results Discussion Brief

Date: 2026-11-02

## One-paragraph summary

The corrected FIR-MINT implementation was evaluated on COCO and Flickr30k with
five seeds. The accepted 4-column and 6-column COCO experiments and the
accepted 4-column Flickr30k experiment met the 0.90 minimum-recall target for
every policy and had zero measured recall-violating mass. FIR-MINT was broadly
comparable to full re-tuning, but the current evidence does not justify a
general claim that it is cheaper: what-if-call savings are small and
inconsistent. The 8-column COCO run completed but failed the recall gate on
seeds 1 and 3, so it is rejected.

## Accepted evidence

### COCO 6 columns

Columns: `I_b32`, `T_b32`, `M_b32`, `T2_b32`, `I_b16`, `T_b16`.

| Policy | Latency (ms) | Min recall | What-if calls | Build (s) |
|---|---:|---:|---:|---:|
| Static | 4.911 ± 0.686 | 0.955 ± 0.058 | 0.0 | 0.000 |
| FIR-MINT | 4.211 ± 0.528 | 0.969 ± 0.033 | 155.8 ± 5.4 | 7.609 ± 1.978 |
| Full re-tune | 4.034 ± 0.578 | 0.966 ± 0.039 | 160.0 ± 5.7 | 9.989 ± 1.931 |

Per-seed FIR-MINT minimum recall: `0.933, 0.989, 0.925, 0.999, 0.999`.
Per-seed Full re-tune minimum recall: `0.940, 0.989, 0.900, 0.999, 0.999`.

### COCO 4 columns

The earlier corrected CPU and H100 runs also passed all recall gates. Their
full tables are in [`EXPERIMENT_RESULTS_ALL.md`](../EXPERIMENT_RESULTS_ALL.md).

### Flickr30k 4 columns

The dataset contains 28,000 data rows and 2,000 query rows with
`I_b32`, `T_b32`, `T2_b32`, and `T3_b32`.

| Policy | Latency (ms) | Min recall | What-if calls | Build (s) |
|---|---:|---:|---:|---:|
| Static | 1.789 ± 0.293 | 0.993 ± 0.003 | 0.0 | 0.000 |
| FIR-MINT | 1.494 ± 0.111 | 0.993 ± 0.003 | 53.4 ± 2.9 | 7.704 ± 3.274 |
| Full re-tune | 1.481 ± 0.090 | 0.994 ± 0.004 | 47.6 ± 1.6 | 8.050 ± 3.035 |

All Flickr30k E1 and E3 recall gates passed, with zero false re-tunes.

## Rejected evidence

The COCO 8-column run is retained for transparency but excluded from claims:

| Seed | FIR-MINT | Full re-tune |
|---:|---:|---:|
| 0 | 0.950 | 0.950 |
| 1 | 0.700 | 0.700 |
| 2 | 0.900 | 0.900 |
| 3 | 0.500 | 0.500 |
| 4 | 0.975 | 0.911 |

See [`rejected_runs/coco8/REASON.txt`](./rejected_runs/coco8/REASON.txt).

## What the results support

1. FIR-MINT can meet the recall constraint on the corrected 4- and 6-column
   COCO configurations.
2. FIR-MINT has measured latency and drift costs close to full re-tuning.
3. Synthetic experiments provide candidate-column scaling evidence through
   12 columns.
4. The two accepted datasets support a cautious multi-dataset claim for
   four-column configurations; the 8-column COCO result remains rejected.

## What the results do not support

- “FIR-MINT is always cheaper than full re-tuning.”
- “FIR-MINT scales successfully to eight real columns.”
- A strong generalization claim beyond the tested COCO and Flickr30k
  configurations.
- Comparison against the real MINT algorithm.
- End-to-end adaptation time under expensive sampled-query recall estimation.
- Sensitivity conclusions for window size, threshold rule, storage budget, or
  recall target.

## Files for discussion

- [`EXPERIMENT_RESULTS_ALL.md`](../EXPERIMENT_RESULTS_ALL.md): complete report
- [`paired_stats_final.md`](./paired_stats_final.md): paired per-seed statistics
- [`coco6/results.md`](./coco6/results.md): accepted 6-column raw report
- [`flickr4/results.md`](./flickr4/results.md): accepted Flickr30k raw report
- [`rejected_runs/coco8/results.md`](./rejected_runs/coco8/results.md): rejected 8-column report
- [`../code_frozen/`](../code_frozen/): frozen source and checksums

## Recommended paper wording

> On corrected COCO and Flickr30k experiments, FIR-MINT satisfied the 0.90
> minimum-recall constraint for every evaluated seed and achieved latency and
> drift costs comparable to full re-tuning. The observed advantage is
> configuration-dependent: current results do not establish lower tuning cost
> in all settings, and an eight-column COCO run failed the recall gate.
> Additional datasets, a faithful MINT comparison, and explicit
> recall-estimation cost measurements are required before making stronger
> claims.
