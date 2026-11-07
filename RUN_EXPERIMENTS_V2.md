# FIR-MINT Paper Experiment Campaign — Runbook V2

**For: Claude Code / GitHub Copilot agent, running on the HPC4DS cluster (UniTN).**
**Goal: produce every result needed for the paper from ONE frozen code version, with a complete, honest record.**

Read this whole file before starting. Execute tasks in order (T0 → T7). After each task, run its checks. If a check fails, stop and report (Section 9). Never present a failed or partial run as a result.

---

## 1. Context (what already exists)

- `fir_mint_v4.py` — the **final** FIR-MINT implementation, already modified during the 30k COCO campaign (tie-aware recall, sampled-minimum recall calibration, pools up to 2,560, HNSW M=32 / efConstruction=128 / efSearch=256, exact `IndexFlatIP` fallback for duplicate-heavy columns, Transformers 5.x fixes).
- Completed: COCO 30k × 4 columns (CLIP B/32), E1 + E3, on the H100 host and the CPU host. All recall gates passed.
- **Not yet done (this runbook):**
  1. code freeze and change log,
  2. synthetic E1/E2/E3 + candidate ablation **re-run with the final code**,
  3. paired per-seed statistics,
  4. real multi-model columns (6 and 8 columns),
  5. second dataset (Flickr30k),
  6. one results bundle and summary.

New helper scripts delivered with this runbook (put them next to `fir_mint_v4.py`):

| File | Purpose |
|---|---|
| `paired_stats.py` | Paired per-seed comparisons with 95% CIs from any `results.json` |
| `embed_multi.py` | Multi-model (CLIP B/32 + B/16) embeddings for COCO and Flickr30k, same rows for every model |
| `make_subset.py` | Builds a k-column vector folder from a larger one |
| `RUN_EXPERIMENTS_V2.md` | This file |

Also required: `fir_mint_v4.py` (final), `ablation_candidates.py`, `coco_embed.py`, the existing PBS script `run_hpc4ds_gpu.pbs`, and the existing 30k COCO vectors.

---

## 2. Hard rules

1. **One code version for all paper results.** After T0, do not modify `fir_mint_v4.py` or `ablation_candidates.py`. The only allowed change is the build-thread patch in Section 6, applied during T0 **before** freezing.
2. Do not change experiment constants (recall target, pools, HNSW parameters, seeds, budget, FIR candidate range, window size). If a run fails because of a constant, stop and report; do not tune constants to make results look better.
3. Do not delete or overwrite earlier results. Every run writes to a new, clearly named folder.
4. Every run must pass its recall gates (Section 8). Runs that fail are kept in `FINAL_RESULTS/rejected_runs/` with a one-line reason, and are never used for claims.
5. Log everything: exact command, host, job ID, start/end time, and exit status, in `FINAL_RESULTS/RUN_LOG.md`.
6. Measured latency (E1) must come from **CPU FAISS**. A GPU is used only for computing embeddings.
7. Report results exactly as produced. If a result is negative or mixed (e.g. FIR worse than Full on some metric), report it plainly.

---

## 3. Directory layout to create

```
$RAO/
├── code_frozen/                 # T0: frozen copy of all scripts + CHANGES.md + SHA256SUMS
├── embeddings/
│   ├── coco_30k_4col_gpu/       # existing
│   ├── coco_30k_8col/           # T3
│   ├── coco_30k_6col/           # T3 (subset)
│   └── flickr_28k_4col/         # T4
├── runs/                        # one folder per run, created by the scripts
└── FINAL_RESULTS/               # T6 bundle
    ├── RUN_LOG.md
    ├── SUMMARY.md
    ├── rejected_runs/
    └── ...
```

Set once per shell:

```bash
export RAO=/path/to/RAO            # adjust to the real project root
export HF_HOME=$RAO/hf_cache
cd $RAO/code_frozen                # after T0, always run from the frozen copy
```

---

## 4. Tasks

### T0 — Freeze the code and document all changes

1. Apply the build-thread patch from Section 6 to `fir_mint_v4.py`, if not already present.
2. Copy into `$RAO/code_frozen/`: `fir_mint_v4.py`, `ablation_candidates.py`, `coco_embed.py`, `embed_multi.py`, `make_subset.py`, `paired_stats.py`, and the PBS scripts.
3. Write `$RAO/code_frozen/CHANGES.md` listing **every** modification made to `fir_mint_v4.py` and `coco_embed.py` since the original v4 version, one entry each with:
   - what changed (old → new value or behaviour),
   - why (which failure it fixed),
   - its effect on results (e.g. "larger pools make merge plans slower for all policies").
   Use `git diff` if the project is a git repository; otherwise reconstruct from the logs and the earlier report.
4. Record checksums:
   ```bash
   cd $RAO/code_frozen && sha256sum *.py *.pbs > SHA256SUMS
   ```
5. Smoke test (must finish without errors in a few minutes):
   ```bash
   python -c "import fir_mint_v4 as F; print(F.RECALL_TARGET, F.POOLS, F.HNSW_M, F.EF_SEARCH, F.SEEDS)"
   ```

**Check:** `CHANGES.md` and `SHA256SUMS` exist; the printed constants match the 30k COCO campaign.

---

### T1 — Synthetic experiments with the final code (CPU host)

Re-run all synthetic experiments so they come from the same code as the real-data results.

```bash
cd $RAO/runs && mkdir -p synthetic && cd synthetic
python $RAO/code_frozen/fir_mint_v4.py            > log_main.txt 2>&1
python $RAO/code_frozen/ablation_candidates.py    > log_ablation.txt 2>&1
```

Note: `ablation_candidates.py` imports `fir_mint_v4`, so run it with `PYTHONPATH=$RAO/code_frozen` if it is not found:
```bash
PYTHONPATH=$RAO/code_frozen python $RAO/code_frozen/ablation_candidates.py > log_ablation.txt 2>&1
```

Expected outputs in `runs/synthetic/fir_mint_v4_results/`: `results.md`, `results.json`, `fig1_measured.png`, `fig2_scaling.png`, `fig3_timelines.png`, `ablation_candidates.md`, `fig4_ablation_candidates.png`.

If the run exceeds the interactive time limit, submit it as a CPU batch job (Section 7).

**Checks:** recall gates (Section 8) pass. E2 table covers 3–12 columns. Ablation covers 6, 8, 12 columns.

---

### T2 — Paired per-seed statistics for existing and new results

```bash
cd $RAO/FINAL_RESULTS
python $RAO/code_frozen/paired_stats.py \
  <path>/fir_mint_v4_results_coco_30k_4col/results.json \
  <path>/fir_mint_v4_results_coco_30k_4col_gpu/results.json \
  $RAO/runs/synthetic/fir_mint_v4_results/results.json \
  --out paired_stats_part1.md
```

Re-run this at the end of T5 including the new runs (Section T6).

**Check:** the file contains E1 and E3 sections for each input.

---

### T3 — Real multi-model columns: COCO 30k with 8 and 6 columns

**3a. Embeddings (GPU host, via PBS).** Same 30,000 data rows and 2,000 query rows for both models (fixed seed 0):

```bash
python $RAO/code_frozen/embed_multi.py --dataset coco --root $RAO/data/coco \
  --models b32 b16 --n_data 30000 --n_query 2000 --seed 0 \
  --out $RAO/embeddings/coco_30k_8col
```

This yields 8 columns: `I_b32 T_b32 M_b32 T2_b32 I_b16 T_b16 M_b16 T2_b16` (all 512-d).
Expected time on the H100: roughly 20–40 minutes. Use `--batch 32` if GPU memory errors occur.

**3b. 6-column subset:**

```bash
python $RAO/code_frozen/make_subset.py --src $RAO/embeddings/coco_30k_8col \
  --out $RAO/embeddings/coco_30k_6col \
  --columns I_b32 T_b32 M_b32 T2_b32 I_b16 T_b16
```

**3c. FIR-MINT runs (CPU host, via PBS, one job each):**

```bash
cd $RAO/runs && python $RAO/code_frozen/fir_mint_v4.py --data $RAO/embeddings/coco_30k_6col > log_coco6.txt 2>&1
cd $RAO/runs && python $RAO/code_frozen/fir_mint_v4.py --data $RAO/embeddings/coco_30k_8col > log_coco8.txt 2>&1
```

These are much heavier than the 4-column run: the estimator builds and caches HNSW indexes for many column combinations (up to 8 singles, 28 pairs, 56 triples). Request a long walltime (e.g. 24 h) and 8 CPUs; the build-thread patch (Section 6) lets index building use them while query timing stays single-threaded.

**Checks:** shapes printed by `embed_multi.py` are `(30000, 512)` / `(2000, 512)` for all 8 columns; recall gates pass for both runs.

---

### T4 — Second dataset: Flickr30k (4 columns, CLIP B/32)

1. Obtain Flickr30k images + captions. The common source is the Kaggle dataset "flickr30k" (images folder plus `results.csv` with `image_name| comment_number| comment`, or `Images/` plus `captions.txt`). Place it under `$RAO/data/flickr30k/`. If no download source is accessible from the cluster, stop and report (the human will download it manually).
2. Embeddings (GPU host):
   ```bash
   python $RAO/code_frozen/embed_multi.py --dataset flickr --root $RAO/data/flickr30k \
     --models b32 --n_data 28000 --n_query 2000 --seed 0 \
     --out $RAO/embeddings/flickr_28k_4col
   ```
   Columns: `I_b32 T_b32 T2_b32 T3_b32`.
3. FIR-MINT (CPU host):
   ```bash
   cd $RAO/runs && python $RAO/code_frozen/fir_mint_v4.py --data $RAO/embeddings/flickr_28k_4col > log_flickr4.txt 2>&1
   ```

**Checks:** about 28,000 data rows and 2,000 query rows; recall gates pass.

---

### T5 — (Optional, only if T1–T4 all passed) COCO 8 columns, second seed set

Skip unless time allows. Purpose: confirm the 8-column result is stable. Requires changing `SEEDS`, which is forbidden by Rule 2, so **do not run this without explicit approval from the human**.

---

### T6 — Paired statistics for everything

```bash
cd $RAO/FINAL_RESULTS
python $RAO/code_frozen/paired_stats.py \
  <coco_30k_4col CPU>/results.json \
  <coco_30k_4col GPU-host>/results.json \
  $RAO/runs/synthetic/fir_mint_v4_results/results.json \
  $RAO/runs/fir_mint_v4_results_coco_30k_6col/results.json \
  $RAO/runs/fir_mint_v4_results_coco_30k_8col/results.json \
  $RAO/runs/fir_mint_v4_results_flickr_28k_4col/results.json \
  --out paired_stats.md
```

---

### T7 — Results bundle and summary

Copy into `$RAO/FINAL_RESULTS/`, one subfolder per run (`coco4_cpu/`, `coco4_gpuhost/`, `coco6/`, `coco8/`, `flickr4/`, `synthetic/`), each with its `results.md`, `results.json`, figures, and log. Also copy `code_frozen/CHANGES.md` and `SHA256SUMS`.

Write `FINAL_RESULTS/SUMMARY.md` with exactly these sections:

1. **Code version:** checksum of `fir_mint_v4.py`, link to `CHANGES.md`.
2. **Runs table:** run name, dataset, rows, columns, host, job ID, wall time, recall gates (pass/fail).
3. **E1 table across datasets** (CPU-host numbers): Static / FIR-MINT / Full re-tune latency, p95, min recall, what-if calls, new indexes, build time.
4. **Paired E1 statistics:** FIR vs Static and FIR vs Full, mean change, 95% CI, seeds better (from `paired_stats.md`).
5. **E3 table across datasets:** post-onset cost per scenario and policy, false re-tunes, what-if calls, index builds.
6. **Scaling evidence:** synthetic E2 (3–12 columns) next to real data (4, 6, 8 columns): what-if calls FIR vs Full and cost ratio FIR/Full.
7. **Ablation:** candidate count K vs speed-up and quality (synthetic).
8. **Honest conclusions:** what the data supports and what it does not. Include negative or mixed findings (e.g. what-if counts, p95 latency) explicitly.
9. **Rejected runs:** list with reasons.

---

## 5. Expected total effort

| Task | Host | Rough time |
|---|---|---|
| T0 | any | < 30 min |
| T1 | CPU | 1–4 h (larger pools and stronger HNSW make it slower than before) |
| T3a | H100 | 20–40 min |
| T3c | CPU | several hours each (6 and 8 columns) |
| T4 | H100 + CPU | 30 min embedding + 1–3 h FIR-MINT |
| T6–T7 | any | < 1 h |

---

## 6. Allowed patch: multi-threaded index building (apply in T0 only)

Index building is the bottleneck for 6–8 columns. Query timing must stay single-threaded, but building may use all CPUs. In `fir_mint_v4.py`, inside `Store.get` (the method that builds an HNSW index), wrap the build like this:

```python
BUILD_THREADS = int(os.environ.get("FIR_BUILD_THREADS", "1"))   # module level; add "import os" at top

# inside Store.get, around the index construction and idx.add(...):
faiss.omp_set_num_threads(BUILD_THREADS)
try:
    ... existing build code, including idx.add(vecs) ...
finally:
    faiss.omp_set_num_threads(1)          # query timing stays single-threaded
```

Apply the same wrapper to the exact `IndexFlatIP` fallback build if it has its own code path. Then run with `export FIR_BUILD_THREADS=8`. Record in `CHANGES.md` that reported build times use 8 threads from this point on; build times are therefore not directly comparable to the earlier 4-column runs, but latency and recall are.

---

## 7. PBS job templates

Adapt from the existing `run_hpc4ds_gpu.pbs`. Use the same environment activation lines as that script.

**GPU embedding job (T3a, T4 step 2):**
```bash
#!/bin/bash
#PBS -q commonGPUQ
#PBS -l select=1:ncpus=8:ngpus=1:mem=64gb:gpu_type=H100
#PBS -l walltime=07:59:00
#PBS -N fir_embed
#PBS -o logs/embed.out
#PBS -e logs/embed.err
cd $RAO/code_frozen
# <environment activation lines copied from run_hpc4ds_gpu.pbs>
export HF_HOME=$RAO/hf_cache
python embed_multi.py --dataset coco --root $RAO/data/coco --models b32 b16 \
  --n_data 30000 --n_query 2000 --seed 0 --out $RAO/embeddings/coco_30k_8col
```

**CPU experiment job (T1, T3c, T4 step 3):**
```bash
#!/bin/bash
#PBS -q <cpu queue used for the earlier CPU run>
#PBS -l select=1:ncpus=8:mem=64gb
#PBS -l walltime=24:00:00
#PBS -N fir_coco8
#PBS -o logs/coco8.out
#PBS -e logs/coco8.err
cd $RAO/runs
# <environment activation lines>
export FIR_BUILD_THREADS=8
python $RAO/code_frozen/fir_mint_v4.py --data $RAO/embeddings/coco_30k_8col
```

Submit with `qsub <file>.pbs`; record the job ID in `RUN_LOG.md`.

---

## 8. Recall gates (every run)

A run is valid only if all of these hold, read from its `results.md`:

1. E1 min recall ≥ 0.90 for **every** policy.
2. E1 recall-violating mass = 0 for every policy.
3. E3 recall-violating mass = 0 for every scenario and policy.
4. E3 false re-tunes = 0 is **expected but not a gate**: if nonzero, keep the run and report the number honestly.

---

## 9. Failure handling

| Situation | Action |
|---|---|
| Out of memory during FIR-MINT | Re-submit with `mem=128gb`. Do not reduce rows without approval. |
| Walltime exceeded | Re-submit with longer walltime. Indexes are rebuilt (no cache on disk), so the full run restarts. |
| Recall gate fails | Move the run to `rejected_runs/` with the reason. Stop and report. Do not change constants. |
| GPU out of memory in `embed_multi.py` | Re-run with `--batch 32`, then `--batch 16`. |
| Flickr30k not downloadable from the cluster | Stop T4 and report; continue with T6–T7 for the other runs. |
| Any other error | Show the full traceback in the report, stop that task, continue with independent tasks if possible. |

---

## 10. Final report to the human

When finished, reply with:
1. the path to `FINAL_RESULTS/`,
2. the full content of `SUMMARY.md`,
3. the full content of `paired_stats.md`,
4. `CHANGES.md`,
5. any task that was skipped or failed, with the reason.
