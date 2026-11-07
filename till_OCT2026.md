# FIR-MINT Project Handoff — Results Through October 2026

This is the compact handoff for continuing the FIR-MINT project from GitHub.
The project was executed on the UniTN HPC4DS cluster. Large reproducible
datasets, model caches, generated embeddings, and the Python environment were
removed from the working copy before publication; the scripts and result
reports remain.

## Repository

- GitHub: https://github.com/Yousaf95/fir_mint
- Local project root before push: `/home/$USER/RAO_OCT`
- Main consolidated context: [`FINAL_RESULTS/CLAUDE_CODE_CONTEXT.md`](FINAL_RESULTS/CLAUDE_CODE_CONTEXT.md)
- Short discussion summary: [`FINAL_RESULTS/SUMMARY.md`](FINAL_RESULTS/SUMMARY.md)
- Full historical report: [`EXPERIMENT_RESULTS_ALL.md`](EXPERIMENT_RESULTS_ALL.md)
- Paired statistics: [`FINAL_RESULTS/paired_stats_final.md`](FINAL_RESULTS/paired_stats_final.md)

## Project goal

Evaluate FIR-MINT as a drift-aware re-tuning loop for multi-vector search,
compared with Static and Full re-tune policies, while enforcing a minimum
recall target of 0.90.

The strongest supported result is:

> Drift-aware adaptation reduces post-onset estimated query cost relative to
> static configurations, while FIR-MINT reaches quality close to full
> re-tuning and preserves the recall constraint.

Do not claim that FIR-MINT is always cheaper than Full re-tune in what-if
calls. The observed savings are small and inconsistent.

## Frozen implementation

All V2 paper results use [`code_frozen/`](code_frozen/). Its changes are
documented in [`code_frozen/CHANGES.md`](code_frozen/CHANGES.md), with
checksums in [`code_frozen/SHA256SUMS`](code_frozen/SHA256SUMS).

Important corrections:

- Tie-aware exact recall with numerical boundary tolerance.
- Sampled-minimum recall calibration instead of average-only calibration.
- Candidate pools through 2,560.
- HNSW `M=32`, `efConstruction=128`, `efSearch=256`.
- Exact `IndexFlatIP` fallback for duplicate-heavy vectors.
- Transformers 5.x CLIP structured-output compatibility.
- `FIR_BUILD_THREADS=8` for index construction; query timing remains one
  FAISS thread.

Common settings:

```text
recall target = 0.90
seeds = 0,1,2,3,4
k = 10
extra storage budget = 8
FIR candidates = 3..8
monitoring window = 300 queries
```

## Completed accepted experiments

### COCO 4 columns

Dataset: 30,000 data rows, 2,000 queries, 512 dimensions per column.
The corrected CPU and H100 runs passed all recall gates.

H100 E1:

| Policy | Latency ms | Min recall | What-if calls |
|---|---:|---:|---:|
| Static | 2.866 ± 0.459 | 0.992 ± 0.006 | 0.0 |
| FIR-MINT | 2.498 ± 0.439 | 0.995 ± 0.006 | 53.8 ± 2.6 |
| Full re-tune | 2.417 ± 0.323 | 0.995 ± 0.006 | 47.2 ± 2.3 |

CPU E1:

| Policy | Latency ms | Min recall | What-if calls |
|---|---:|---:|---:|
| Static | 2.647 ± 0.693 | 0.992 ± 0.004 | 0.0 |
| FIR-MINT | 1.999 ± 0.295 | 0.995 ± 0.004 | 54.8 ± 3.8 |
| Full re-tune | 2.056 ± 0.231 | 0.995 ± 0.004 | 45.8 ± 2.2 |

### COCO 6 columns

Columns: `I_b32`, `T_b32`, `M_b32`, `T2_b32`, `I_b16`, `T_b16`.
Dataset: 30,000 data rows and 2,000 queries.

| Policy | Latency ms | p95 ms | Min recall | What-if calls | Build s |
|---|---:|---:|---:|---:|---:|
| Static | 4.911 ± 0.686 | 11.532 ± 0.878 | 0.955 ± 0.058 | 0.0 | 0.000 |
| FIR-MINT | 4.211 ± 0.528 | 11.228 ± 0.709 | 0.969 ± 0.033 | 155.8 ± 5.4 | 7.609 ± 1.978 |
| Full re-tune | 4.034 ± 0.578 | 10.342 ± 1.708 | 0.966 ± 0.039 | 160.0 ± 5.7 | 9.989 ± 1.931 |

Per-seed minimum recall:

- FIR-MINT: `0.933, 0.989, 0.925, 0.999, 0.999`
- Full re-tune: `0.940, 0.989, 0.900, 0.999, 0.999`

### Flickr30k 4 columns

Dataset: 28,000 data rows and 2,000 queries. Columns:
`I_b32`, `T_b32`, `T2_b32`, `T3_b32`.

| Policy | Latency ms | p95 ms | Min recall | What-if calls | Build s |
|---|---:|---:|---:|---:|---:|
| Static | 1.789 ± 0.293 | 3.745 ± 1.038 | 0.993 ± 0.003 | 0.0 | 0.000 |
| FIR-MINT | 1.494 ± 0.111 | 2.724 ± 0.085 | 0.993 ± 0.003 | 53.4 ± 2.9 | 7.704 ± 3.274 |
| Full re-tune | 1.481 ± 0.090 | 2.735 ± 0.106 | 0.994 ± 0.004 | 47.6 ± 1.6 | 8.050 ± 3.035 |

All E1 and E3 recall gates passed. False re-tunes were zero.

## Synthetic evidence

Frozen-code synthetic main and candidate-ablation runs completed. E2 scaling
covers 3, 4, 5, 6, 8, 10, and 12 columns; candidate ablation covers 6, 8,
and 12 columns.

Outputs are in [`runs/synthetic/`](runs/synthetic/). Use these results for
scaling and ablation evidence, not as a substitute for real data.

## Rejected experiment

The COCO 8-column run completed technically but failed the E1 recall gate:

| Seed | FIR-MINT min recall | Full re-tune min recall |
|---:|---:|---:|
| 0 | 0.950 | 0.950 |
| 1 | 0.700 | 0.700 |
| 2 | 0.900 | 0.900 |
| 3 | 0.500 | 0.500 |
| 4 | 0.975 | 0.911 |

It is preserved under [`FINAL_RESULTS/rejected_runs/coco8/`](FINAL_RESULTS/rejected_runs/coco8/)
and must not be used for positive claims. The JSON stores aggregate recall,
not the discarded per-query-type recall. A future diagnostic copy should save
that value before changing the frozen implementation.

## E3 interpretation

Across accepted COCO, Flickr30k, and synthetic runs:

- Drift-aware adaptation reduces post-onset estimated cost versus Static.
- FIR+detector is close to Full+detector.
- False re-tunes are zero.
- Full-every-window makes many more what-if calls.
- p95 latency does not consistently improve; typical latency is stronger
  evidence.

Representative COCO 6-column FIR+detector versus Static E3 changes:

| Scenario | Mean post-onset change | 95% CI | Seeds better |
|---|---:|---:|---:|
| Abrupt | -21.6% | [-30.8%, -12.5%] | 5/5 |
| Gradual | -17.8% | [-29.6%, -6.0%] | 5/5 |
| Recurring | -11.1% | [-20.1%, -2.1%] | 5/5 |
| New type | -30.9% | [-56.7%, -5.1%] | 5/5 |

## Reproduction status after cleanup

The following heavy, reproducible artifacts were intentionally deleted before
the GitHub push:

- COCO raw data: `data/`
- Flickr30k raw data/cache: `kaggle_cache/`
- Hugging Face/model cache: `cache/`
- Project Python environment: `venv/`
- Generated NumPy embeddings: `embeddings/`

They can be regenerated with the scripts and PBS templates. The preserved
results are the source of truth for the completed runs.

The preserved source includes:

- `fir_mint_v4.py`
- `coco_embed.py`
- `embed_multi.py`
- `make_subset.py`
- `paired_stats.py`
- `ablation_candidates.py`
- `code_frozen/`
- PBS scripts for COCO and Flickr
- experiment instructions and runbooks
- raw result JSON, Markdown, figures, and logs

## HPC job history

- COCO 6-column CPU: `413257.hpc3-head1.unitn.it`
- COCO 8-column CPU: `413258.hpc3-head1.unitn.it`
- Flickr H100 embeddings: `418548.hpc3-head1.unitn.it`
- Flickr CPU FIR-MINT: `418968.hpc3-head1.unitn.it`

The Flickr H100 embedding job validated all arrays as `(28000, 512)` and
`(2000, 512)`. The Flickr CPU FIR-MINT job completed in 206 seconds.

## Remaining work

For a workshop paper, the accepted COCO + Flickr30k results, synthetic
scaling, frozen code, rejected-run disclosure, and paired statistics are a
reasonable evidence package.

For a stronger venue:

1. Instrument and diagnose the COCO 8-column per-query-type recall failure.
2. Compare against the real MINT algorithm or a faithful reimplementation.
3. Measure expensive sampled-query recall-estimation cost.
4. Measure end-to-end adaptation time: detection, tuning, build, switch-over.
5. Run focused sensitivity analyses: window, threshold, budget, recall target.
6. Add related work on online index tuning, drift detection, and multi-vector
   search.

## Storage after cleanup

The home quota dropped from approximately 223 GB to **187 GB / 240 GB** after
deleting the approved artifacts. The repository itself is now only a few
megabytes and is suitable for GitHub.
