# FIR-MINT Experiment Campaign — Complete Claude Code Context

Date: 2026-11-03  
Project: `/home/$USER/RAO_OCT`

This file is the single shareable context document for discussing the
experiments with Claude Code. It consolidates the completed campaign,
accepted and rejected results, commands, implementation changes, limitations,
and next steps. Raw JSON, figures, logs, frozen source, and detailed tables
remain in the linked result folders.

## 1. Executive conclusion

The corrected FIR-MINT implementation meets the 0.90 minimum-recall target on
the accepted COCO 4-column, COCO 6-column, and Flickr30k 4-column runs, with
zero measured recall-violating mass and zero false re-tunes. Under drift,
FIR-MINT reduces post-onset estimated query cost relative to static
configurations and is close to full re-tuning. The strongest defensible claim
is that drift-aware warm-start tuning matches full re-tuning quality while
preserving recall constraints.

Do not claim that FIR-MINT is always cheaper than full re-tuning in what-if
calls. The savings are small and inconsistent. Do not claim successful
eight-column real-data scaling: the COCO 8-column run failed recall on some
seeds and is explicitly rejected.

## 2. Paper-ready claim

> We propose a drift-aware re-tuning loop for multi-vector index
> configurations. On corrected COCO and Flickr30k experiments, FIR-MINT
> satisfied the 0.90 minimum-recall constraint for every accepted seed and
> achieved latency and drift costs comparable to full re-tuning. Under
> workload drift, adaptation reduced post-onset estimated cost relative to
> static configurations, while the warm-start tuner remained close to full
> re-tuning. The advantage is configuration-dependent: current experiments do
> not establish lower what-if cost in every setting, and an eight-column COCO
> run failed the recall gate.

## 3. Environment and hardware

Project root:

```text
/home/$USER/RAO_OCT
```

Software:

- Python 3.11.5
- PyTorch 2.15.0+cu132
- Transformers 5.22.1
- FAISS 1.15.1
- NumPy, Pillow, Matplotlib, tqdm

H100 embedding host:

- Host: `hpc3-g06-n01.unitn.it`
- Queue: `commonGPUQ`
- Resource request: 1 H100, 8 CPUs, 64 GB RAM
- GPU: NVIDIA H100 NVL, approximately 95 GB memory

CPU FIR-MINT host:

- Queue: `commonCPUQ`
- Resource request: 1 node, 8 CPUs, 64 GB RAM
- `FIR_BUILD_THREADS=8`
- Query timing resets FAISS to one thread

The GPU nodes cannot access `/data`; all GPU inputs, models, environments,
embeddings, logs, and outputs are under `/home`.

## 4. Frozen implementation

All V2 paper results use the frozen source in
[`code_frozen/`](../code_frozen/). Do not modify it for new claims without
creating a new explicitly versioned experiment.

Important correctness changes:

1. Tie-aware exact recall with numerical boundary tolerance.
2. Conservative sampled-minimum recall calibration instead of average-only
   calibration.
3. Candidate pools through 2,560.
4. HNSW `M=32`, `efConstruction=128`, and `efSearch=256`.
5. Exact `IndexFlatIP` fallback for duplicate-heavy single-column vectors.
6. Transformers 5.x CLIP structured-output compatibility.
7. Optional eight-thread index construction via `FIR_BUILD_THREADS`.

Frozen documentation and checksums:

- [`CHANGES.md`](../code_frozen/CHANGES.md)
- [`SHA256SUMS`](../code_frozen/SHA256SUMS)
- [`fir_mint_v4.py`](../code_frozen/fir_mint_v4.py)
- [`embed_multi.py`](../code_frozen/embed_multi.py)
- [`paired_stats.py`](../code_frozen/paired_stats.py)
- [`RUN_EXPERIMENTS_V2.md`](../RUN_EXPERIMENTS_V2.md)

## 5. Common experiment settings

```text
recall target       = 0.90
seeds               = 0, 1, 2, 3, 4
k                   = 10
pool                = 40
HNSW M              = 32
efConstruction      = 128
efSearch            = 256
extra storage       = 8
FIR candidates      = 3..8
candidate coverage  = 80%
monitoring window   = 300 queries
```

Formal recall gates:

1. Every E1 policy and seed has minimum recall at least 0.90.
2. E1 recall-violating mass is zero.
3. E3 recall-violating mass is zero.
4. E3 false re-tunes are reported; accepted runs have zero.

## 6. Datasets and embeddings

### COCO

- COCO 2017 Option A
- 118,287 train images and 5,000 validation images available
- 30,000 data rows
- 2,000 query rows
- 512 dimensions per vector
- L2-normalized CLIP vectors
- Original 4-column content: image, caption 1, category text, caption 2

COCO 4-column vectors:

[`embeddings/coco_30k_4col`](../embeddings/coco_30k_4col) and
[`embeddings/coco_30k_4col_gpu`](../embeddings/coco_30k_4col_gpu)

COCO 8-column vectors use CLIP B/32 and B/16:

`I_b32`, `T_b32`, `M_b32`, `T2_b32`, `I_b16`, `T_b16`, `M_b16`, `T2_b16`

[`embeddings/coco_30k_8col`](../embeddings/coco_30k_8col)

The accepted six-column subset is:

`I_b32`, `T_b32`, `M_b32`, `T2_b32`, `I_b16`, `T_b16`

[`embeddings/coco_30k_6col`](../embeddings/coco_30k_6col)

### Flickr30k

- KaggleHub dataset: `hsankesara/flickr-image-dataset`
- 28,000 data rows
- 2,000 query rows
- Four CLIP B/32 columns:
  `I_b32`, `T_b32`, `T2_b32`, `T3_b32`
- All data/query arrays are `(28000, 512)` and `(2000, 512)`

The image collection is stored only in the KaggleHub cache; it was not copied:

[`kaggle_cache/`](../../kaggle_cache)

Flickr embeddings:

[`embeddings/flickr_28k_4col`](../embeddings/flickr_28k_4col)

## 7. Accepted COCO 6-column results

Raw report:
[`coco6/results.md`](./coco6/results.md)  
Raw JSON:
[`coco6/results.json`](./coco6/results.json)  
Execution log:
[`coco6/coco6_cpu.out`](./coco6/coco6_cpu.out)

E1 values are mean ± standard deviation over five seeds:

| Policy | Latency ms | p95 ms | Min recall | What-if calls | New indexes | Build s |
|---|---:|---:|---:|---:|---:|---:|
| Static | 4.911 ± 0.686 | 11.532 ± 0.878 | 0.955 ± 0.058 | 0.0 | 0.0 | 0.000 |
| FIR-MINT | 4.211 ± 0.528 | 11.228 ± 0.709 | 0.969 ± 0.033 | 155.8 ± 5.4 | 2.2 ± 0.7 | 7.609 ± 1.978 |
| Full re-tune | 4.034 ± 0.578 | 10.342 ± 1.708 | 0.966 ± 0.039 | 160.0 ± 5.7 | 2.8 ± 0.7 | 9.989 ± 1.931 |

Per-seed minimum recall:

- FIR-MINT: `0.933, 0.989, 0.925, 0.999, 0.999`
- Full re-tune: `0.940, 0.989, 0.900, 0.999, 0.999`

All E1 and E3 recall gates passed.

## 8. Accepted Flickr30k 4-column results

Raw report:
[`flickr4/results.md`](./flickr4/results.md)  
Raw JSON:
[`flickr4/results.json`](./flickr4/results.json)  
Execution log:
[`flickr4/flickr4_cpu.out`](./flickr4/flickr4_cpu.out)

E1 values are mean ± standard deviation over five seeds:

| Policy | Latency ms | p95 ms | Min recall | What-if calls | New indexes | Build s |
|---|---:|---:|---:|---:|---:|---:|
| Static | 1.789 ± 0.293 | 3.745 ± 1.038 | 0.993 ± 0.003 | 0.0 | 0.0 | 0.000 |
| FIR-MINT | 1.494 ± 0.111 | 2.724 ± 0.085 | 0.993 ± 0.003 | 53.4 ± 2.9 | 2.0 ± 0.9 | 7.704 ± 3.274 |
| Full re-tune | 1.481 ± 0.090 | 2.735 ± 0.106 | 0.994 ± 0.004 | 47.6 ± 1.6 | 2.2 ± 0.7 | 8.050 ± 3.035 |

Per-seed E1 minimum recall was at least 0.9875 for every policy. All E1 and
E3 recall gates passed. E3 false re-tunes were zero.

## 9. Earlier accepted COCO 4-column results

The earlier corrected CPU and H100 COCO runs also passed all recall gates.
Full tables are in [`EXPERIMENT_RESULTS_ALL.md`](../EXPERIMENT_RESULTS_ALL.md).

H100 E1:

| Policy | Latency ms | Min recall | What-if calls | New indexes | Build s |
|---|---:|---:|---:|---:|---:|
| Static | 2.866 ± 0.459 | 0.992 ± 0.006 | 0.0 | 0.0 | 0.000 |
| FIR-MINT | 2.498 ± 0.439 | 0.995 ± 0.006 | 53.8 ± 2.6 | 1.6 ± 0.5 | 22.200 ± 7.194 |
| Full re-tune | 2.417 ± 0.323 | 0.995 ± 0.006 | 47.2 ± 2.3 | 1.6 ± 0.5 | 22.136 ± 7.133 |

CPU E1:

| Policy | Latency ms | Min recall | What-if calls | New indexes | Build s |
|---|---:|---:|---:|---:|---:|
| Static | 2.647 ± 0.693 | 0.992 ± 0.004 | 0.0 | 0.0 | 0.000 |
| FIR-MINT | 1.999 ± 0.295 | 0.995 ± 0.004 | 54.8 ± 3.8 | 1.8 ± 0.7 | 25.341 ± 6.348 |
| Full re-tune | 2.056 ± 0.231 | 0.995 ± 0.004 | 45.8 ± 2.2 | 2.0 ± 1.1 | 27.697 ± 10.004 |

## 10. E3 interpretation

E3 compares Static, FIR+detector, Full+detector, and Full every window over
abrupt, gradual, recurring, and new-type drift. The detailed per-dataset
tables are in the raw `results.md` files and the paired analysis.

The consistent finding across accepted COCO, Flickr30k, and synthetic runs is:

- Drift-aware adaptation reduces post-onset estimated cost relative to Static.
- FIR+detector is very close to Full+detector.
- False re-tunes are zero.
- Full-every-window is a strong cost baseline but pays many more what-if calls.
- p95 latency is not consistently improved; typical latency is the stronger
  result.

Representative paired COCO 6-column E3 changes for FIR+detector versus Static:

| Scenario | Mean post-onset change | 95% CI | Seeds better |
|---|---:|---:|---:|
| Abrupt | -21.6% | [-30.8%, -12.5%] | 5/5 |
| Gradual | -17.8% | [-29.6%, -6.0%] | 5/5 |
| Recurring | -11.1% | [-20.1%, -2.1%] | 5/5 |
| New type | -30.9% | [-56.7%, -5.1%] | 5/5 |

Flickr30k E3 accepted results are recorded in
[`flickr4/results.md`](./flickr4/results.md). Synthetic and all paired
comparisons are in [`paired_stats_final.md`](./paired_stats_final.md).

## 11. Synthetic evidence

Frozen-code synthetic main and candidate-ablation experiments completed.
Synthetic E2 scaling covers 3, 4, 5, 6, 8, 10, and 12 columns. Candidate
ablation covers 6, 8, and 12 columns.

Outputs:

- [`runs/synthetic/fir_mint_v4_results`](../runs/synthetic/fir_mint_v4_results)
- [`runs/synthetic/log_main.txt`](../runs/synthetic/log_main.txt)
- [`runs/synthetic/log_ablation.txt`](../runs/synthetic/log_ablation.txt)

Use synthetic results as scaling/ablation evidence only; do not present them
as real-data validation.

## 12. Rejected COCO 8-column run

Raw rejected run:
[`rejected_runs/coco8/results.md`](./rejected_runs/coco8/results.md)  
Raw JSON:
[`rejected_runs/coco8/results.json`](./rejected_runs/coco8/results.json)  
Reason:
[`rejected_runs/coco8/REASON.txt`](./rejected_runs/coco8/REASON.txt)

E1 minimum recall:

| Seed | FIR-MINT | Full re-tune |
|---:|---:|---:|
| 0 | 0.950 | 0.950 |
| 1 | 0.700 | 0.700 |
| 2 | 0.900 | 0.900 |
| 3 | 0.500 | 0.500 |
| 4 | 0.975 | 0.911 |

The failures are identical for FIR-MINT and Full re-tune on the worst seeds,
which suggests an estimator/index/plan problem rather than a clear tuner
comparison. However, the JSON does not contain `per_type_recall`; it stores
only aggregate E1/E3 rows and configurations. A diagnostic copy would need to
save the currently discarded per-query-type values before any code change.

This run must remain excluded from positive claims.

## 13. Paired statistics

Final paired statistics:
[`paired_stats_final.md`](./paired_stats_final.md)

The script uses paired per-seed comparisons and 95% t-distribution confidence
intervals. Negative percentage means the first policy has lower latency/cost.

Main interpretation:

- FIR vs Static is often beneficial for E1 latency, but CPU E1 intervals can
  cross zero.
- FIR vs Full is usually close to zero, commonly within approximately 0–2%.
- E3 adaptation versus Static is the strongest and most consistent result.
- FIR does not consistently improve p95 latency.
- What-if savings versus Full are not a universal result.

## 14. Complete report and final summary

- [`EXPERIMENT_RESULTS_ALL.md`](../EXPERIMENT_RESULTS_ALL.md): complete historical and final report
- [`SUMMARY.md`](./SUMMARY.md): short discussion/paper brief
- [`paired_stats_final.md`](./paired_stats_final.md): final paired statistics

This file is the recommended single document to share with Claude Code.

## 15. Commands and job history

COCO multi-model H100 embedding:

```bash
qsub /home/$USER/RAO_OCT/embed_multi_gpu.pbs
```

COCO CPU runs:

```bash
qsub /home/$USER/RAO_OCT/run_coco6_cpu.pbs
qsub /home/$USER/RAO_OCT/run_coco8_cpu.pbs
```

Flickr H100 embedding:

```bash
qsub /home/$USER/RAO_OCT/embed_flickr_gpu.pbs
```

Flickr CPU FIR-MINT:

```bash
qsub /home/$USER/RAO_OCT/run_flickr4_cpu.pbs
```

Completed job IDs:

- COCO 6-column CPU: `413257.hpc3-head1.unitn.it`
- COCO 8-column CPU: `413258.hpc3-head1.unitn.it`
- Flickr H100 embeddings: `418548.hpc3-head1.unitn.it`
- Flickr CPU FIR-MINT: `418968.hpc3-head1.unitn.it`

The Flickr H100 embedding job ran for approximately 13 minutes and produced
all validated arrays. The Flickr CPU FIR-MINT job completed in 206 seconds.

## 16. Known failures and historical fixes

The initial 30,000-row CPU run was rejected because minimum recall was
approximately 0.670–0.729 and violation mass was nonzero. It is not used for
claims.

Transformers 5.x returned structured CLIP outputs rather than tensors. The
embedding code now extracts `pooler_output`, `image_embeds`, or
`text_embeds` as appropriate.

Initial average-recall calibration did not protect individual query types.
The final frozen implementation uses sampled minimum recall, larger pools,
stronger HNSW settings, tie-aware recall, and exact indexing for duplicate
heavy columns.

## 17. Storage and quota

The project was moved from `/data` to home because GPU nodes cannot access
`/data`. The old `/data/$USER/RAO_NOV` project was removed
after validation.

Most recent observed home quota after Flickr completion:

- Used: approximately 223 GB
- Soft quota: 240 GB
- Remaining before soft quota: approximately 17 GB

Avoid creating duplicate dataset copies. The 8.7 GB Flickr dataset remains in
the KaggleHub cache and the Flickr embeddings use approximately 236 MB.

## 18. Remaining work and recommendation

For a workshop paper, the accepted COCO + Flickr30k results, synthetic
scaling, frozen code, rejected-run disclosure, and honest claim boundary are
already a reasonable evidence package. Start writing now.

For a stronger main-track submission, the highest-value remaining experiments
are:

1. Save `per_type_recall` in a diagnostic copy and investigate the 8-column
   failure without altering the frozen results.
2. Compare against the real MINT algorithm, or clearly label a faithful
   reimplementation if source code is unavailable.
3. Measure expensive sampled-query recall estimation cost.
4. Measure end-to-end adaptation time: detection delay, tuning, index build,
   and switch-over.
5. Run focused sensitivity analyses for window size, detector threshold,
   storage budget, and recall target.
6. Add related work on online index tuning, what-if optimization, drift
   detection, and multi-vector search.

Do not add arbitrary seeds or variations merely to make tables larger. The
remaining questions are methodological, not a need for more repetitions.
