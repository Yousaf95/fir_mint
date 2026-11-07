# FIR-MINT Experiment Instructions for HPC4DS

## Purpose

Run the corrected FIR-MINT experiments directly on HPC4DS using the shared
data directory:

```text
/data/$USER/RAO_NOV
```

Do not use `/home` for datasets, model caches, vectors, or large outputs.
The user's home quota is nearly full. The `/data` filesystem has approximately
1.2 TB available.

Work step by step. After each checkpoint, verify the command output before
continuing.

## Current project files

The corrected source files have already been copied to:

```text
/data/$USER/RAO_NOV/src/
```

Expected files:

```text
RUN_EXPERIMENTS.md
fir_mint_v4.py
coco_embed.py
ablation_candidates.py
EXPERIMENT_PLAN_GPU.md
```

The copied `fir_mint_v4.py` includes the tie-aware `recall_of()` fix. Do not
replace it with an older copy.

## Important storage paths

Set these variables at the start of every shell session:

```bash
export RAO=/data/$USER/RAO_NOV
export COCO=$RAO/data/coco
export HF_HOME=$RAO/cache/huggingface
```

Create the required directories:

```bash
mkdir -p "$RAO"/{src,cache,data,embeddings,results,logs}
mkdir -p "$HF_HOME"
cd "$RAO"
```

Check storage:

```bash
hostname
df -h "$RAO"
quota -s
```

## 1. Load the HPC software modules

The available modules include Python 3.11 and CUDA 12.6. Load:

```bash
module load Python/3.11.5-GCCcore-13.2.0
module load CUDA/12.6.0
```

Verify:

```bash
python --version
which python
nvcc --version
```

Expected Python is 3.11.x.

Check whether this host exposes a GPU:

```bash
command -v nvidia-smi || true
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>/dev/null || true
```

If `nvidia-smi` is unavailable, do not claim GPU acceleration. Continue only
if the cluster documentation confirms that HPC4DS is a GPU execution host or
if a supported CUDA device is visible through another documented mechanism.
The CLIP embedding script automatically selects CUDA only when
`torch.cuda.is_available()` is true.

## 2. Create an isolated environment

Create the environment outside `/home` if the cluster supports a virtual
environment on `/data`:

```bash
python -m venv "$RAO/venv"
source "$RAO/venv/bin/activate"
python -m pip install --upgrade pip
```

Install the required packages:

```bash
python -m pip install numpy matplotlib tqdm pillow transformers
```

Install a PyTorch build compatible with the loaded CUDA module and the cluster
driver. Prefer the cluster's documented PyTorch module or wheel. Do not
install a CPU-only wheel when a GPU is available.

Verify:

```bash
python - <<'PY'
import torch
print("torch:", torch.__version__)
print("cuda available:", torch.cuda.is_available())
if torch.cuda.is_available():
    print("device:", torch.cuda.get_device_name(0))
PY
```

Also install or load FAISS:

```bash
python -c "import faiss; print('faiss:', faiss.__version__)"
```

If FAISS is not available, install `faiss-cpu`. The current FIR-MINT index
implementation uses FAISS CPU indexes even when embeddings are generated on a
GPU.

Do not continue until Python, PyTorch, Transformers, Pillow, NumPy, tqdm,
Matplotlib, and FAISS import successfully.

## 3. Confirm the corrected source

Run:

```bash
cd "$RAO"
cp "$RAO/src/fir_mint_v4.py" "$RAO/"
cp "$RAO/src/coco_embed.py" "$RAO/"
cp "$RAO/src/RUN_EXPERIMENTS.md" "$RAO/"
python -m py_compile "$RAO/fir_mint_v4.py" "$RAO/coco_embed.py"
grep -n -A7 "def recall_of" "$RAO/fir_mint_v4.py"
```

The recall function must compute the exact score boundary and include all
items tied at that boundary. It must not use an arbitrary exact top-k set as
the only ground truth.

## 4. Download COCO Option A

Use the shared data directory:

```bash
mkdir -p "$COCO"
cd "$COCO"
```

Download:

```bash
curl -fL -C - -o train2017.zip \
  http://images.cocodataset.org/zips/train2017.zip
curl -fL -C - -o val2017.zip \
  http://images.cocodataset.org/zips/val2017.zip
curl -fL -C - -o annotations_trainval2017.zip \
  http://images.cocodataset.org/annotations/annotations_trainval2017.zip
```

Test and extract:

```bash
unzip -t train2017.zip
unzip -t val2017.zip
unzip -t annotations_trainval2017.zip
unzip -q train2017.zip
unzip -q val2017.zip
unzip -q annotations_trainval2017.zip
```

Verify:

```bash
test -d "$COCO/train2017"
test -d "$COCO/val2017"
test -f "$COCO/annotations/captions_train2017.json"
test -f "$COCO/annotations/captions_val2017.json"
test -f "$COCO/annotations/instances_train2017.json"
test -f "$COCO/annotations/instances_val2017.json"
find "$COCO/train2017" -maxdepth 1 -name '*.jpg' | wc -l
find "$COCO/val2017" -maxdepth 1 -name '*.jpg' | wc -l
```

Expected image counts are approximately 118,287 train images and 5,000
validation images.

## 5. Generate 30k COCO vectors

Use the model cache on `/data`:

```bash
export HF_HOME=$RAO/cache/huggingface
mkdir -p "$HF_HOME"
cd "$RAO"
```

Run:

```bash
python coco_embed.py \
  --coco_root "$COCO" \
  --n_data 30000 \
  --n_query 2000 \
  --out "$RAO/embeddings/coco_30k_4col" \
  2>&1 | tee "$RAO/logs/coco_30k_embedding.log"
```

The expected columns are:

```text
I, T, M, T2
```

Validate:

```bash
python - <<'PY'
import json
import numpy as np
from pathlib import Path

p = Path("embeddings/coco_30k_4col")
cols = json.loads((p / "meta.json").read_text())["columns"]
assert tuple(cols) == ("I", "T", "M", "T2")
for c in cols:
    d = np.load(p / f"data_{c}.npy")
    q = np.load(p / f"query_{c}.npy")
    print(c, "data", d.shape, "query", q.shape)
    assert d.shape[0] >= 30000
    assert d.shape[1] == 512
    assert q.shape == (2000, 512)
PY
```

If CUDA is unavailable, stop and report that the run is CPU-only before
starting a long embedding job. Do not silently describe it as a GPU result.

## 6. Run corrected FIR-MINT on 30k COCO

Run with a unique output folder name:

```bash
cd "$RAO"
python fir_mint_v4.py \
  --data "$RAO/embeddings/coco_30k_4col" \
  2>&1 | tee "$RAO/logs/coco_30k_firmint.log"
```

The script writes results to:

```text
$RAO/fir_mint_v4_results_coco_30k_4col/
```

Verify:

```bash
test -s "$RAO/fir_mint_v4_results_coco_30k_4col/results.md"
test -s "$RAO/fir_mint_v4_results_coco_30k_4col/results.json"
test -s "$RAO/fir_mint_v4_results_coco_30k_4col/fig1_measured.png"
test -s "$RAO/fir_mint_v4_results_coco_30k_4col/fig3_timelines.png"
```

Read `results.md` and enforce these gates:

- E1 minimum recall is at least 0.90 for Static, FIR-MINT, and Full re-tune.
- E1 recall-violating mass is zero for all three policies.
- E3 recall-violating mass is zero.
- E3 false re-tunes are zero.

If any gate fails, stop and report the failure. Do not present latency or
efficiency claims as valid until the recall issue is resolved.

## 7. Build the additional real-column dataset

The target is six or more real columns using the same row IDs and query IDs:

```text
I_CLIP   image embedding from CLIP
I_DINO   image embedding from DINOv2
T_CLIP   caption embedding from CLIP
T_ST     caption embedding from a sentence transformer
M        object-category text embedding
T2_CLIP  second caption embedding from CLIP
```

All arrays in one FIR-MINT folder must have the same dimension. If model
dimensions differ, use a documented fixed projection and record it in
`meta.json`; never silently concatenate incompatible dimensions.

Store:

```text
$RAO/embeddings/coco_30k_6col/
├── data_<column>.npy
├── query_<column>.npy
└── meta.json
```

The metadata must record the model/version, source IDs, split IDs, dimensions,
normalization, and any projection:

```json
{
  "columns": ["I_CLIP", "I_DINO", "T_CLIP", "T_ST", "M", "T2_CLIP"],
  "model_by_column": {},
  "data_ids": [],
  "query_ids": [],
  "projection": {}
}
```

Run:

```bash
cd "$RAO"
python fir_mint_v4.py \
  --data "$RAO/embeddings/coco_30k_6col" \
  2>&1 | tee "$RAO/logs/coco_30k_6col_firmint.log"
```

Apply the same recall gates.

## 8. Second dataset

After COCO passes all gates, prepare Flickr30k under:

```text
$RAO/data/flickr30k
$RAO/embeddings/flickr30k_6col
```

Use the same file format, held-out query protocol, metadata fields, and recall
gates. Preserve dataset license/readme files and record the source URL in
`meta.json`.

Run:

```bash
cd "$RAO"
python fir_mint_v4.py \
  --data "$RAO/embeddings/flickr30k_6col" \
  2>&1 | tee "$RAO/logs/flickr30k_6col_firmint.log"
```

## 9. Sensitivity runs

Run unique copies of the experiment for:

```text
window size:     150, 300, 600
threshold rule:  mean + 3 standard deviations, 95th percentile
budget:          4, 8, 12
recall target:   0.90, 0.95, 0.99
```

For each run, record:

- latency and p95 latency
- minimum recall
- recall-violating mass
- retune count
- false-retune count
- what-if calls
- index builds
- estimator time
- configuration-search time
- index-build time
- detection delay
- switch-over time
- total adaptation time

Keep the default corrected COCO run unchanged as the baseline.

## 10. Final report

Create:

```text
$RAO/EXPERIMENT_RESULTS_HPC4DS.md
```

The report must contain only:

1. Hardware and software environment.
2. Dataset sizes and splits.
3. Embedding columns and model metadata.
4. Exact commands used.
5. E1 tables.
6. E3 tables.
7. Sensitivity tables.
8. Output file locations.
9. Recall and reproducibility checks.
10. Any failed or skipped run, clearly labeled.

Do not claim GPU execution unless the run records:

```bash
hostname
nvidia-smi
python -c "import torch; print(torch.cuda.is_available())"
```

Do not claim that all policies satisfy recall unless the generated results show
zero recall-violating mass and minimum recall at least 0.90.

## Current known baseline

The corrected local baseline used COCO Option B:

```text
data rows: 3962
query rows: 990
columns: I, T, M, T2
```

Corrected E1:

| Policy | Latency (ms) | Min recall | Recall-violating mass | What-if calls |
|---|---:|---:|---:|---:|
| Static | 0.557 ± 0.084 | 0.979 ± 0.006 | 0.000 ± 0.000 | 0 |
| FIR-MINT | 0.445 ± 0.085 | 0.983 ± 0.009 | 0.000 ± 0.000 | 48.8 ± 2.8 |
| Full re-tune | 0.452 ± 0.056 | 0.983 ± 0.009 | 0.000 ± 0.000 | 44.0 ± 1.9 |

These values are a reference only. The HPC4DS results must be reported
separately and must not overwrite this baseline.
