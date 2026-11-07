# FIR-MINT HPC4DS Experiment Results

Date: 2026-11-02

## 1. Scope

This report records every experiment run completed in this project. The completed
real-data campaign is MSCOCO 2017 with four CLIP-derived vector columns:

- `I`: image embedding
- `T`: caption 1 embedding
- `M`: object-category text embedding
- `T2`: caption 2 embedding

The V2 campaign subsequently completed corrected 6-column and 8-column COCO
runs, a corrected Flickr30k run, synthetic reruns, and paired statistics. The
8-column COCO run failed the per-seed recall gate and is reported only as a
rejected run. The real MINT implementation/reimplementation, expensive
sampled-recall timing, end-to-end adaptation decomposition, and sensitivity
campaigns remain incomplete.

## 2. Final hardware and software

### CPU execution host

- Host: `hpc4ds`
- Python: 3.11.5
- PyTorch: 2.15.0+cu132
- Transformers: 5.22.1
- FAISS: 1.15.1
- CUDA visible: `False`

### H100 execution host

- Host: `hpc3-g06-n01.unitn.it`
- Queue: `commonGPUQ`
- Allocation: 1 GPU, 8 CPUs, 64 GB RAM
- GPU: NVIDIA H100 NVL
- Driver: 595.71.05
- CUDA reported by `nvidia-smi`: 13.2
- Python: 3.11.5
- PyTorch: 2.15.0+cu132
- CUDA visible: `True`

The H100 job was submitted as:

```bash
qsub run_hpc4ds_gpu.pbs
```

PBS request:

```text
qsub -q commonGPUQ \
  -l select=1:ncpus=8:ngpus=1:mem=64gb:gpu_type=H100 \
  -l walltime=07:59:00
```

## 3. Dataset and vector generation

COCO Option A was downloaded and extracted:

- Train images: 118,287
- Validation images: 5,000
- Train/validation captions and instances annotations: present
- Data rows: 30,000 sampled from `train2017`
- Query rows: 2,000 sampled from `val2017`
- Columns: `I`, `T`, `M`, `T2`
- Dimension per column: 512
- Model: `openai/clip-vit-base-patch32`
- All vectors: L2-normalized

Embedding command:

```bash
python coco_embed.py \
  --coco_root "$RAO/data/coco" \
  --n_data 30000 \
  --n_query 2000 \
  --out "$RAO/embeddings/coco_30k_4col_gpu"
```

Validated shapes:

| Column | Data shape | Query shape |
|---|---:|---:|
| I | `(30000, 512)` | `(2000, 512)` |
| T | `(30000, 512)` | `(2000, 512)` |
| M | `(30000, 512)` | `(2000, 512)` |
| T2 | `(30000, 512)` | `(2000, 512)` |

## 4. Correctness changes

The final source includes:

1. Tie-aware exact ground truth using a numerical boundary tolerance.
2. Correct handling of tied boundary items.
3. Conservative sampled-minimum recall calibration for merge plans.
4. Candidate pools through 2,560.
5. Stronger HNSW settings:
   - `M=32`
   - `efConstruction=128`
   - `efSearch=256`
6. Exact `IndexFlatIP` fallback for duplicate-heavy single-column vectors.

The category-text column contains many duplicate vectors, so the exact fallback
is required for reliable recall measurement.

## 5. Final H100 COCO run

FIR-MINT settings:

```text
N=30000
dim/column=512
k=10
recall target=0.90
extra storage budget=8
FIR candidates=3..8
candidate coverage=80%
monitoring window=300 queries
seeds=5
HNSW M=32
efSearch=256
```

### E1: measured performance after abrupt drift

| Policy | Latency (ms) | p95 (ms) | Min recall | Recall-violating mass | What-if calls | Tuning (s) | New indexes | Build (s) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Static | 2.866 ± 0.459 | 6.927 ± 1.591 | 0.992 ± 0.006 | 0.000 ± 0.000 | 0.0 ± 0.0 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| FIR-MINT | 2.498 ± 0.439 | 7.493 ± 2.010 | 0.995 ± 0.006 | 0.000 ± 0.000 | 53.8 ± 2.638 | 0.001 ± 0.000 | 1.600 ± 0.490 | 22.200 ± 7.194 |
| Full re-tune | 2.417 ± 0.323 | 6.879 ± 1.544 | 0.995 ± 0.006 | 0.000 ± 0.000 | 47.2 ± 2.315 | 0.000 ± 0.000 | 1.600 ± 0.490 | 22.136 ± 7.133 |

### E3: drift scenarios

| Scenario | Policy | Mean cost (ms) | Post-onset cost (ms) | Recall-violating mass | Re-tunes | False re-tunes | What-if calls | Index builds |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| abrupt | Static | 3.003 ± 0.982 | 2.873 ± 0.937 | 0.000 | 0.0 | 0.0 | 0 | 0.0 |
| abrupt | FIR+detector | 2.875 ± 0.889 | 2.681 ± 0.788 | 0.000 | 1.0 | 0.0 | 52 | 1.4 |
| abrupt | Full+detector | 2.920 ± 0.949 | 2.749 ± 0.884 | 0.000 | 1.0 | 0.0 | 48 | 1.8 |
| abrupt | Full every window | 2.919 ± 0.911 | 2.745 ± 0.854 | 0.000 | 0.0 | 0.0 | 1377 | 24.8 |
| gradual | Static | 3.430 ± 0.901 | 3.565 ± 0.931 | 0.000 | 0.0 | 0.0 | 0 | 0.0 |
| gradual | FIR+detector | 3.152 ± 1.098 | 3.147 ± 1.165 | 0.000 | 2.8 | 0.0 | 131 | 2.8 |
| gradual | Full+detector | 3.170 ± 1.098 | 3.174 ± 1.178 | 0.000 | 2.8 | 0.0 | 131 | 4.4 |
| gradual | Full every window | 3.169 ± 1.125 | 3.163 ± 1.204 | 0.000 | 0.0 | 0.0 | 1341 | 29.8 |
| recurring | Static | 3.329 ± 0.912 | 3.346 ± 0.854 | 0.000 | 0.0 | 0.0 | 0 | 0.0 |
| recurring | FIR+detector | 3.205 ± 1.026 | 3.177 ± 0.987 | 0.000 | 3.0 | 0.0 | 153 | 5.8 |
| recurring | Full+detector | 3.225 ± 1.003 | 3.204 ± 0.961 | 0.000 | 3.0 | 0.0 | 139 | 6.4 |
| recurring | Full every window | 3.207 ± 1.027 | 3.179 ± 0.992 | 0.000 | 0.0 | 0.0 | 1333 | 26.0 |
| new_type | Static | 3.950 ± 1.677 | 4.296 ± 2.130 | 0.000 | 0.0 | 0.0 | 0 | 0.0 |
| new_type | FIR+detector | 2.772 ± 1.041 | 2.529 ± 0.886 | 0.000 | 1.0 | 0.0 | 48 | 2.0 |
| new_type | Full+detector | 2.774 ± 1.047 | 2.532 ± 0.896 | 0.000 | 1.0 | 0.0 | 47 | 1.6 |
| new_type | Full every window | 2.691 ± 1.007 | 2.406 ± 0.822 | 0.000 | 0.0 | 0.0 | 1219 | 27.0 |

### H100 recall gates

- E1 minimum recall for every policy: at least 0.90: **passed**
- E1 recall-violating mass: zero: **passed**
- E3 recall-violating mass: zero: **passed**
- E3 false re-tunes: zero: **passed**

## 6. CPU COCO run

The same corrected experiment was run on the CPU host with the same 30,000-row
COCO vectors and final recall-safe implementation.

### E1

| Policy | Latency (ms) | p95 (ms) | Min recall | Recall-violating mass | What-if calls | Tuning (s) | New indexes | Build (s) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Static | 2.647 ± 0.693 | 6.865 ± 1.197 | 0.992 ± 0.004 | 0.000 ± 0.000 | 0.0 ± 0.0 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| FIR-MINT | 1.999 ± 0.295 | 6.712 ± 1.056 | 0.995 ± 0.004 | 0.000 ± 0.000 | 54.8 ± 3.763 | 0.001 ± 0.000 | 1.800 ± 0.748 | 25.341 ± 6.348 |
| Full re-tune | 2.056 ± 0.231 | 6.959 ± 0.767 | 0.995 ± 0.004 | 0.000 ± 0.000 | 45.8 ± 2.227 | 0.001 ± 0.000 | 2.000 ± 1.095 | 27.697 ± 10.004 |

The CPU E3 table is preserved in:

[CPU results](./results/fir_mint_v4_results_coco_30k_4col/results.md)

## 7. Earlier failed runs and fixes

### Initial CPU run

The first 30k run produced low recall:

- E1 minimum recall approximately 0.670–0.729
- Recall-violating mass was nonzero

It was rejected and not used for claims.

### Transformers compatibility failure

Transformers 5.x returned `BaseModelOutputWithPooling` from CLIP feature
methods. The embedding code was updated to extract `pooler_output`, then the
30k embedding job was rerun successfully.

### Recall calibration and index fixes

The initial average-recall calibration did not protect individual queries.
The final implementation uses conservative sampled-minimum calibration,
stronger HNSW parameters, duplicate-safe exact indexing, and numerical tie
handling. The final H100 and CPU runs both pass all recall gates.

## 8. Output files

- [H100 PBS script](./run_hpc4ds_gpu.pbs)
- [Final FIR-MINT source](./fir_mint_v4.py)
- [COCO embedding script](./coco_embed.py)
- [H100 E1/E3 Markdown](./fir_mint_v4_results_coco_30k_4col_gpu/results.md)
- [H100 raw results](./fir_mint_v4_results_coco_30k_4col_gpu/results.json)
- [H100 measured figure](./fir_mint_v4_results_coco_30k_4col_gpu/fig1_measured.png)
- [H100 timeline figure](./fir_mint_v4_results_coco_30k_4col_gpu/fig3_timelines.png)
- [H100 execution log](./logs/pbs-gpu.out)
- [H100 embedding log](./logs/coco_30k_gpu_embedding.log)
- [H100 FIR-MINT log](./logs/coco_30k_gpu_firmint.log)
- [CPU results](./results/fir_mint_v4_results_coco_30k_4col/results.md)
- [CPU raw results](./results/fir_mint_v4_results_coco_30k_4col/results.json)

## 9. Honest conclusion

On the completed COCO four-column experiment, FIR-MINT matches full re-tuning
recall quality and has zero measured recall violations. Its measured E1
what-if count is higher than full re-tuning in this implementation, so this
campaign does not support a claim that FIR-MINT is cheaper in what-if calls.
The results support the narrower statement that FIR-MINT achieves the recall
target and comparable measured latency/quality to full re-tuning on this
dataset and configuration.

## 10. V2 campaign status and final evidence

All V2 paper results use the frozen source under
[`code_frozen/`](./code_frozen/), with recall target 0.90, five seeds, 30,000
COCO data rows, 2,000 queries, and 512-dimensional vectors.

### Accepted COCO 6-column run

The six columns are `I_b32`, `T_b32`, `M_b32`, `T2_b32`, `I_b16`, and `T_b16`.
The run completed successfully on the CPU queue and passed the formal recall
gates for every seed and policy.

| Policy | Mean latency (ms) | Min recall | What-if calls | New indexes | Build (s) |
|---|---:|---:|---:|---:|---:|
| Static | 4.911 ± 0.686 | 0.955 ± 0.058 | 0.0 | 0.0 | 0.000 |
| FIR-MINT | 4.211 ± 0.528 | 0.969 ± 0.033 | 155.8 ± 5.4 | 2.2 ± 0.7 | 7.609 ± 1.978 |
| Full re-tune | 4.034 ± 0.578 | 0.966 ± 0.039 | 160.0 ± 5.7 | 2.8 ± 0.7 | 9.989 ± 1.931 |

Per-seed minimum recall passed for FIR-MINT:
`0.933, 0.989, 0.925, 0.999, 0.999`; and for Full re-tune:
`0.940, 0.989, 0.900, 0.999, 0.999`.

Files: [`COCO 6-column results`](./FINAL_RESULTS/coco6/results.md),
[`raw JSON`](./FINAL_RESULTS/coco6/results.json), and
[`CPU log`](./FINAL_RESULTS/coco6/coco6_cpu.out).

### Rejected COCO 8-column run

The eight-column run completed technically, but it must not support positive
claims because the E1 minimum-recall gate failed:

| Seed | FIR-MINT min recall | Full re-tune min recall |
|---:|---:|---:|
| 0 | 0.950 | 0.950 |
| 1 | 0.700 | 0.700 |
| 2 | 0.900 | 0.900 |
| 3 | 0.500 | 0.500 |
| 4 | 0.975 | 0.911 |

The run is preserved in
[`rejected_runs/coco8/`](./FINAL_RESULTS/rejected_runs/coco8/) with the reason
in [`REASON.txt`](./FINAL_RESULTS/rejected_runs/coco8/REASON.txt).

### Synthetic and paired analyses

The frozen-code synthetic main and candidate-ablation runs completed, including
6-, 8-, and 12-column scaling. The consolidated paired analysis is in
[`paired_stats_final.md`](./FINAL_RESULTS/paired_stats_final.md). These
statistics use paired seeds and 95% t-distribution confidence intervals.

### Current claim boundary

The defensible claim is:

> On the corrected 4-column and accepted 6-column COCO experiments, FIR-MINT
> meets the 0.90 recall target with zero measured recall-violating mass and
> achieves performance broadly comparable to full re-tuning.

Do **not** currently claim that FIR-MINT is cheaper than full re-tuning in
what-if calls: in the accepted 6-column E1 run it used 155.8 versus 160.0
calls, while in earlier 4-column runs it was not consistently lower. Do not
claim successful real-data scaling to eight columns because that run failed
recall. The two-dataset evidence is limited to the tested COCO and Flickr30k
configurations; avoid broader generalization claims.

### Reproducibility and remaining work

- Project root: `/home/$USER/RAO_OCT`
- Frozen code and checksums: [`code_frozen/`](./code_frozen/)
- Final paired statistics: [`FINAL_RESULTS/paired_stats_final.md`](./FINAL_RESULTS/paired_stats_final.md)
- Flickr30k: downloaded and processed through the KaggleHub cache; no duplicate
  image copy was created.
- Still required for the stronger paper claims: a real MINT comparison,
  expensive sampled-query recall-cost measurements, end-to-end adaptation time,
  and sensitivity analyses.

## 11. Flickr30k final results

Flickr30k was downloaded from the supplied KaggleHub dataset and processed
without copying the image collection. The accepted run used 28,000 data rows,
2,000 query rows, four CLIP B/32 columns (`I_b32`, `T_b32`, `T2_b32`, `T3_b32`),
and five seeds.

| Policy | Latency (ms) | p95 (ms) | Min recall | What-if calls | New indexes | Build (s) |
|---|---:|---:|---:|---:|---:|---:|
| Static | 1.789 ± 0.293 | 3.745 ± 1.038 | 0.993 ± 0.003 | 0.0 | 0.0 | 0.000 |
| FIR-MINT | 1.494 ± 0.111 | 2.724 ± 0.085 | 0.993 ± 0.003 | 53.4 ± 2.9 | 2.0 ± 0.9 | 7.704 ± 3.274 |
| Full re-tune | 1.481 ± 0.090 | 2.735 ± 0.106 | 0.994 ± 0.004 | 47.6 ± 1.6 | 2.2 ± 0.7 | 8.050 ± 3.035 |

All Flickr30k E1 policies and seeds met the 0.90 minimum-recall target with
zero violation mass. All E3 scenarios also had zero violation mass and zero
false re-tunes.

Files: [`Flickr30k results`](./FINAL_RESULTS/flickr4/results.md),
[`raw JSON`](./FINAL_RESULTS/flickr4/results.json), and
[`CPU log`](./FINAL_RESULTS/flickr4/flickr4_cpu.out).
