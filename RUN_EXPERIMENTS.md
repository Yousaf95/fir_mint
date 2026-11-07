# FIR-MINT Experiment Runbook

**Instructions for GitHub Copilot (agent mode) and for the human running it.**
Follow the steps in order. Run each command from the project folder. Do not change experiment parameters, algorithms, or seeds unless a step explicitly says so. If a step fails, use the Troubleshooting section, then retry the same step.

---

## 1. What this project is

FIR-MINT (Fast Incremental Re-Tuning for Multi-Vector Index Optimization) extends MINT (Zhu et al., arXiv:2504.20018, 2025). MINT picks a set of vector indexes for a fixed query workload. FIR-MINT adds:

1. a **drift detector**: KL divergence between query-type histograms, bootstrap threshold (mean + 3 std), sustained-drift rule and cooldown;
2. a **warm-start re-tuner (FIR)**: benefit-aware candidate selection plus add-and-repair local search, starting from the current configuration;
3. **MINT-style estimators**: calibrated latency and recall per plan, with recall target 0.90 enforced for every policy.

Experiments:

| ID | What it measures | Data |
|---|---|---|
| E1 | Measured FAISS HNSW latency and recall after drift: Static vs FIR vs Full re-tune | synthetic and COCO |
| E2 | Tuning effort vs number of vector columns (3 to 12) | synthetic only |
| E3 | Four drift scenarios over 30 windows: abrupt, gradual, recurring, new query type | synthetic and COCO |
| Ablation | FIR candidate count K vs speed-up and quality | synthetic only |

The synthetic results are already done. **The main goal of this runbook is the real-data run on MSCOCO + CLIP (Steps 5 to 7).** Steps 3 and 4 are optional re-checks.

---

## 2. Required files

Put these in one folder, for example `C:\Users\<you>\fir_mint_project\`:

```
fir_mint_project/
├── RUN_EXPERIMENTS.md        (this file)
├── fir_mint_v4.py            (main experiment code: E1, E2, E3; --data for real vectors)
├── ablation_candidates.py    (candidate-count ablation, synthetic)
└── coco_embed.py             (builds CLIP vectors from MSCOCO)
```

`ablation_candidates.py` imports `fir_mint_v4.py`, so both must be in the same folder.

---

## 3. Environment setup

Python 3.10 or 3.11 is recommended (FAISS wheels are most reliable there).

### Windows (PowerShell, VS Code terminal)

```powershell
cd C:\Users\<you>\fir_mint_project
python -m venv fir_env
.\fir_env\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install numpy matplotlib faiss-cpu tqdm pillow transformers
```

Install PyTorch:

- With an NVIDIA GPU: get the exact command from https://pytorch.org/get-started/locally/ (choose pip + your CUDA version).
- CPU only:
  ```powershell
  pip install torch
  ```

### Linux / macOS

```bash
python3 -m venv fir_env && source fir_env/bin/activate
pip install --upgrade pip
pip install numpy matplotlib faiss-cpu tqdm pillow transformers torch
```

### Verify

```powershell
python -c "import numpy, faiss, matplotlib, torch, transformers; print('faiss', faiss.__version__, '| torch', torch.__version__, '| cuda', torch.cuda.is_available())"
```

Expected: versions print with no error. `cuda True` is optional; it only speeds up Step 6.

---

## 4. (Optional) Re-run the synthetic experiments

Skip this unless you want to reproduce the existing results. Takes about 5–15 minutes on a normal PC.

```powershell
python fir_mint_v4.py
python ablation_candidates.py
```

Outputs go to `fir_mint_v4_results/`:

- `results.md`, `results.json`
- `fig1_measured.png`, `fig2_scaling.png`, `fig3_timelines.png`
- `ablation_candidates.md`, `fig4_ablation_candidates.png`

**Sanity check**, using the reference values from the completed run. Exact numbers vary by machine, but the pattern should hold:

- E1: FIR latency is lower than Static (reference: about −18%), and min recall is about 0.90 for all policies.
- E3: "False re-tunes" is 0 in every row. FIR+detector cost is within about 1% of Full+detector.
- E2: cost ratio FIR/Full is between 1.00 and 1.02 for every column count.

---

## 5. Download MSCOCO

Source: https://cocodataset.org/#download

Choose **one** option.

### Option A — full (recommended, ~19 GB)

Download:
- `2017 Train images [118K/18GB]`
- `2017 Val images [5K/1GB]`
- `2017 Train/Val annotations [241MB]`

### Option B — lightweight (~1.2 GB)

Download only:
- `2017 Val images [5K/1GB]`
- `2017 Train/Val annotations [241MB]`

### Folder layout after unzipping (example `D:\coco`)

```
D:\coco\
├── train2017\        (Option A only, *.jpg)
├── val2017\          (*.jpg)
└── annotations\
    ├── captions_train2017.json
    ├── captions_val2017.json
    ├── instances_train2017.json
    └── instances_val2017.json
```

Verify:

```powershell
Test-Path D:\coco\val2017; Test-Path D:\coco\annotations\captions_val2017.json; Test-Path D:\coco\annotations\instances_val2017.json
```

All three must print `True`. For Option A, also check `Test-Path D:\coco\train2017`.

---

## 6. Build CLIP vectors

The first run downloads the CLIP model `openai/clip-vit-base-patch32` (~600 MB) from Hugging Face automatically.

### Option A (full)

```powershell
python coco_embed.py --coco_root D:/coco --n_data 30000 --n_query 2000 --out coco_vectors
```

Time: about 15–30 min with a GPU, about 2–4 h on CPU.

### Option B (val2017 only)

```powershell
python coco_embed.py --coco_root D:/coco --val_only --out coco_vectors
```

Time: about 3–5 min with a GPU, about 20–40 min on CPU.

### Expected result

Printed lines like:
```
data: 30000 rows x 4 columns x 512 dims
query: 2000 rows x 4 columns x 512 dims
```
(Option B prints about 3900–4000 data rows and about 1000 query rows.)

Folder `coco_vectors/` contains 9 files:
```
data_I.npy  data_T.npy  data_M.npy  data_T2.npy
query_I.npy query_T.npy query_M.npy query_T2.npy
meta.json
```

The columns are: `I` = image, `T` = caption 1, `M` = object-category text, `T2` = caption 2. All are 512-dim, L2-normalized CLIP vectors.

Verify:

```powershell
python -c "import numpy as np; [print(c, np.load(f'coco_vectors/data_{c}.npy').shape, np.load(f'coco_vectors/query_{c}.npy').shape) for c in ['I','T','M','T2']]"
```

---

## 7. Run FIR-MINT on the real vectors

```powershell
python fir_mint_v4.py --data coco_vectors
```

This runs E1 and E3 with C = 4 real columns (E2 and the ablation are synthetic-only by design).

Expected first line:
```
Real data: 30000 rows, 4 columns ['I', 'T', 'M', 'T2'], dim=512, 2000 held-out queries
```

Time: roughly 20–60 min on CPU for Option A, because HNSW indexes over 1024- and 1536-dim joint vectors take a while to build. Progress lines like `[E1 seed 0] ...` and `[E3 seed 0] ...` print as it goes. Do not interrupt it.

Outputs go to `fir_mint_v4_results_coco_vectors/`:
- `results.md` (main tables)
- `results.json` (raw per-seed data)
- `fig1_measured.png`, `fig3_timelines.png`

---

## 8. What to send back

Send these files (or paste their contents) into the chat:

1. `fir_mint_v4_results_coco_vectors/results.md`
2. `fir_mint_v4_results_coco_vectors/fig1_measured.png`
3. `fir_mint_v4_results_coco_vectors/fig3_timelines.png`
4. Which COCO option you used (A or B), and whether you had a GPU.
5. If you re-ran Step 4: `fir_mint_v4_results/results.md` and `ablation_candidates.md`.

---

## 9. Troubleshooting

| Problem | Fix |
|---|---|
| `Activate.ps1 cannot be loaded because running scripts is disabled` | Run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, then activate again. |
| `pip install faiss-cpu` fails | Use Python 3.10 or 3.11 in a fresh venv. Alternative: `conda install -c pytorch faiss-cpu`. |
| `OMP: Error #15: Initializing libiomp5md.dll, but found libiomp5md.dll already initialized` (Windows, torch + faiss) | Before running, set `$env:KMP_DUPLICATE_LIB_OK="TRUE"` in the same PowerShell session. |
| `FileNotFoundError` for annotations or images | Check the folder layout in Step 5. `--coco_root` must point to the folder that **contains** `val2017` and `annotations`. Use forward slashes: `D:/coco`. |
| CUDA out of memory in `coco_embed.py` | Lower the batch size: in `coco_embed.py`, change `bs=64` in `def embed(...)` to `bs=16`. |
| `coco_embed.py` is too slow on CPU | Use Option B (`--val_only`), or lower `--n_data` to 10000. |
| Hugging Face download fails or times out | Retry. Behind a proxy, set `HTTPS_PROXY`. You can also download the model once with `python -c "from transformers import CLIPModel, CLIPProcessor; CLIPModel.from_pretrained('openai/clip-vit-base-patch32'); CLIPProcessor.from_pretrained('openai/clip-vit-base-patch32')"`. |
| `MemoryError` during `fir_mint_v4.py --data` | Re-run Step 6 with a smaller `--n_data` (e.g. 15000). |
| Step 7 is very slow | Expected on CPU. If it is unacceptable, re-run Step 6 with `--n_data 10000`. |
| `ModuleNotFoundError: fir_mint_v4` when running the ablation | Run from the folder that contains both scripts. |

---

## 10. Rules for Copilot

- Run commands exactly as written. Use the activated `fir_env` interpreter.
- Do **not** change constants in `fir_mint_v4.py` (`RECALL_TARGET`, `POOLS`, `SEEDS`, `EXTRA_BUDGET`, `FIR_KMIN`/`FIR_KMAX`, `HNSW_M`, `EF_SEARCH`, `WIN`) or any algorithm code. The results must stay comparable with the synthetic run.
- The only allowed edits are the Troubleshooting fixes above (batch size, data size via command-line flags, environment variables).
- If a command fails, show the full error message, apply the matching fix from Section 9, and retry. If no fix matches, stop and report the error. Do not improvise code changes.
- When finished, list the output files from Step 8 and show the content of `results.md`.
