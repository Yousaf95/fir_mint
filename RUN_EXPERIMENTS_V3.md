# FIR-MINT Baselines Campaign — Runbook V3 (E4 baselines + E5 detector sensitivity)

**For: Claude Code / GitHub Copilot agent on HPC4DS.** Read the whole file first. Same rules as V2: no changes to frozen code, no tuning of constants, failed runs kept and reported, results reported exactly as produced.

## 1. What this adds

`fir_baselines.py` (new file) imports the frozen `fir_mint_v4.py` and evaluates, on the same estimator-based cost model as E3 and on identical window samples:

- **E4 baselines** for the four drift scenarios: Static, FIR+detector (ours), Full+detector, Oracle (hindsight full re-tune every window), Continuous FIR (no detector, COLT-style), Cost-trigger+FIR (alerter-style), Capped-full+detector (budget-aware, what-if budget = FIR's), Forecast+FIR (QueryBot5000-style), Robust static (CliffGuard-style min-max).
- **E5 detector sensitivity**: window size {150, 300, 600} × threshold k·σ {2, 3, 4}.

It does **not** modify `fir_mint_v4.py` and does not change any existing result.

## 2. Setup (T0)

1. Copy `fir_baselines.py` into `$RAO/code_frozen/`.
2. Append to `$RAO/code_frozen/CHANGES.md`:
   ```
   ## V3 (baselines campaign)
   - Added fir_baselines.py (new file; imports frozen fir_mint_v4.py, no modification).
   ```
3. Record its checksum (do not overwrite the old file):
   ```bash
   cd $RAO/code_frozen && sha256sum fir_baselines.py > SHA256SUMS_V3 && sha256sum -c SHA256SUMS
   ```
   The second command must report `OK` for every previously frozen file. If not, stop and report.
4. API check (must print `API OK`):
   ```bash
   cd $RAO/code_frozen && python -c "import fir_baselines as B; B.check_api(); print('API OK')"
   ```
   If it reports missing names, stop and report. Do not edit either file.
5. Smoke test (about 10–60 s):
   ```bash
   cd $RAO/runs && mkdir -p smoke_v3 && cd smoke_v3
   PYTHONPATH=$RAO/code_frozen python $RAO/code_frozen/fir_baselines.py --seeds 0 --skip_sensitivity --out ./smoke
   ```
   Check that `smoke/baselines.md` contains four scenario tables with nine policies each.

## 2b. Regenerate embeddings first (raw data and embeddings were deleted before the GitHub push)

Home quota is about 187/240 GB. Work on **one dataset at a time** and delete raw data as soon as its embeddings are validated. Order of priority: **Flickr30k (required)**, then COCO 6-column (optional, only if quota allows), then COCO 4-column (optional).

**Flickr30k (required, about 9 GB download):**
1. Download `hsankesara/flickr-image-dataset` (KaggleHub or Kaggle CLI) into `$RAO/data/flickr30k/`. Delete the zip after extraction.
2. GPU job (adapt `embed_flickr_gpu.pbs`):
   ```bash
   python $RAO/code_frozen/embed_multi.py --dataset flickr --root <flickr30k root> \
     --models b32 --n_data 28000 --n_query 2000 --seed 0 --out $RAO/embeddings/flickr_28k_4col
   ```
3. Validate shapes `(28000, 512)` / `(2000, 512)` for `I_b32 T_b32 T2_b32 T3_b32`, then compare `ids.json` with the earlier run if it is available. Delete the raw Flickr data.

**COCO 6-column (optional, needs about 38 GB peak: download and unzip train2017 + val2017 + annotations one archive at a time, deleting each zip after extraction):**
1. GPU job (adapt `embed_multi_gpu.pbs`): `embed_multi.py --dataset coco --root <coco> --models b32 b16 --n_data 30000 --n_query 2000 --seed 0 --out $RAO/embeddings/coco_30k_8col`
2. `make_subset.py --src $RAO/embeddings/coco_30k_8col --out $RAO/embeddings/coco_30k_6col --columns I_b32 T_b32 M_b32 T2_b32 I_b16 T_b16`
3. Validate shapes, delete the raw COCO data and the 8-column folder if quota is tight.

Record in `RUN_LOG.md` that V3 uses **regenerated** embeddings from the same scripts and seed. Small floating-point differences from the earlier embeddings are expected; V3 results are compared only within V3 (all policies on the same regenerated vectors).

## 3. Runs (T1–T4), one PBS CPU job each

All with `PYTHONPATH=$RAO/code_frozen`, `FIR_BUILD_THREADS=8`, CPU queue, 8 CPUs, 64 GB, walltime 24 h for real data and 4 h for synthetic.

| Task | Command | Output folder |
|---|---|---|
| T1 synthetic | **Already done** (run against the frozen `fir_mint_v4.py` from the repo; results in `baselines_synthetic/`). Copy that folder to `FINAL_RESULTS/baselines/synthetic/`; re-running on the cluster is optional. | `runs/baselines_synthetic/` |
| T2 COCO 4 col (optional) | `python $RAO/code_frozen/fir_baselines.py --data <COCO 30k 4-col vectors used for the accepted CPU run> --out $RAO/runs/baselines_coco4` | `runs/baselines_coco4/` |
| T3 COCO 6 col (optional) | `python $RAO/code_frozen/fir_baselines.py --data $RAO/embeddings/coco_30k_6col --out $RAO/runs/baselines_coco6` | `runs/baselines_coco6/` |
| T4 Flickr 4 col (**required, run first**) | `python $RAO/code_frozen/fir_baselines.py --data $RAO/embeddings/flickr_28k_4col --out $RAO/runs/baselines_flickr4` | `runs/baselines_flickr4/` |

Do **not** run the rejected COCO 8-column vectors.

PBS template (adapt the environment lines from the existing CPU scripts):
```bash
#!/bin/bash
#PBS -q commonCPUQ
#PBS -l select=1:ncpus=8:mem=64gb
#PBS -l walltime=24:00:00
#PBS -N fir_base_coco6
#PBS -o logs/base_coco6.out
#PBS -e logs/base_coco6.err
cd $RAO/runs
# <environment activation lines>
export PYTHONPATH=$RAO/code_frozen
export FIR_BUILD_THREADS=8
python $RAO/code_frozen/fir_baselines.py --data $RAO/embeddings/coco_30k_6col --out $RAO/runs/baselines_coco6
```

Each output folder contains `baselines.md`, `baselines.json`, `fig5_baselines.png`.

## 4. Checks for every run

1. Recall: the "Viol. mass" column is 0.000 for every policy except possibly Static and Robust static. If FIR+detector, Full+detector or Oracle shows nonzero violation, move the run to `FINAL_RESULTS/rejected_runs/` with the reason and report.
2. Completeness: four scenarios × nine policies; E5 table present (36 rows).
3. Record command, job ID, host, wall time and exit status in `FINAL_RESULTS/RUN_LOG.md`.

Expected pattern from a reference synthetic run (for orientation only; do not tune to match): Static and Robust static clearly worse than adaptive policies; FIR+detector close to Full+detector; Continuous FIR slightly lower cost but many more what-if calls, index builds and re-tunes before drift onset.

## 5. Bundle

Copy each output folder to `FINAL_RESULTS/baselines/<synthetic|coco4|coco6|flickr4>/`. Then reply with:
1. the full content of each `baselines.md`,
2. the four `fig5_baselines.png` files,
3. run log entries and any rejected run with reason.
