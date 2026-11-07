# FIR-MINT GPU Experiment Plan

## Goal

Continue the corrected FIR-MINT experiment on the H100 node using:

```text
/data/$USER/RAO_NOV
```

Keep the COCO images, downloaded models, generated vectors, logs, figures, and
reports under that directory. The work starts from the corrected tie-aware
recall implementation already applied to `fir_mint_v4.py`.

The final campaign should produce:

1. A corrected COCO run with at least 30,000 data rows.
2. A second multimodal dataset, preferably Flickr30k.
3. Six to eight real vector columns using multiple embedding models.
4. E1 and E3 results with every policy meeting the 0.90 recall target.
5. Sensitivity results for monitoring window, drift threshold, storage budget,
   and recall target.
6. Raw JSON, Markdown tables, figures, and execution logs.

## Current corrected baseline

The existing local COCO Option B run used 3,962 data rows, 990 held-out
queries, and four 512-dimensional columns:

```text
I, T, M, T2
```

The corrected recall implementation is tie-aware. It treats all items tied at
the exact top-k boundary as relevant instead of selecting an arbitrary subset
from `np.argpartition`.

Corrected E1 results:

| Policy | Latency (ms) | Min recall | Recall-violating mass | What-if calls |
|---|---:|---:|---:|---:|
| Static | 0.557 ± 0.084 | 0.979 ± 0.006 | 0.000 ± 0.000 | 0 |
| FIR-MINT | 0.445 ± 0.085 | 0.983 ± 0.009 | 0.000 ± 0.000 | 48.8 ± 2.8 |
| Full re-tune | 0.452 ± 0.056 | 0.983 ± 0.009 | 0.000 ± 0.000 | 44.0 ± 1.9 |

These are the baseline values to preserve. Do not overwrite them without
keeping a copy of the old result directory.

## 1. Prepare the remote directory

Run on the H100 compute node:

```bash
export RAO=/data/$USER/RAO_NOV
mkdir -p "$RAO"/{src,cache,data,embeddings,results,logs}
cd "$RAO"
df -h "$RAO"
quota -s
```

Do not use the home directory for COCO images or the model cache.

## 2. Copy the corrected project

Run from the local YSF terminal, where `/mnt/d/RAO` exists:

```bash
export REMOTE=$USER@<cluster-login-host>
export RAO=/data/$USER/RAO_NOV

scp /mnt/d/RAO/RUN_EXPERIMENTS.md \
    /mnt/d/RAO/fir_mint_v4.py \
    /mnt/d/RAO/coco_embed.py \
    /mnt/d/RAO/ablation_candidates.py \
    "$REMOTE:$RAO/src/"
```

Copy this plan too:

```bash
scp /mnt/d/RAO/EXPERIMENT_PLAN_GPU.md "$REMOTE:$RAO/"
```

On the compute node:

```bash
cd "$RAO"
cp src/fir_mint_v4.py .
cp src/coco_embed.py .
cp src/RUN_EXPERIMENTS.md .
```

The source copy must retain the tie-aware `recall_of()` implementation.

## 3. Create and verify the GPU environment

Use the cluster's supported Python/Conda setup. Do not install packages into
the base environment:

```bash
conda create -n firmint-gpu python=3.11 -y
conda activate firmint-gpu
python -m pip install --upgrade pip
python -m pip install numpy matplotlib tqdm pillow transformers
```

Install the cluster-compatible CUDA PyTorch build. Prefer the cluster's
documented CUDA module or PyTorch wheel. Do not install a CPU-only wheel.

Verify:

```bash
python - <<'PY'
import torch
print("torch:", torch.__version__)
print("cuda:", torch.cuda.is_available())
print("device:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "NONE")
PY
```

The run must not continue unless `cuda: True` and the device is an H100.

FAISS must also be available:

```bash
python -c "import faiss; print('faiss:', faiss.__version__)"
```

If the cluster provides a prebuilt FAISS module, use it. Otherwise install
`faiss-cpu`; the H100 accelerates CLIP/DINO/text embedding, while the current
FIR-MINT FAISS index implementation remains CPU-based.

## 4. Download COCO Option A on the H100 node

Use the storage directory, not home:

```bash
export COCO=$RAO/data/coco
mkdir -p "$COCO"
cd "$COCO"

curl -fL -C - -o train2017.zip \
  http://images.cocodataset.org/zips/train2017.zip
curl -fL -C - -o val2017.zip \
  http://images.cocodataset.org/zips/val2017.zip
curl -fL -C - -o annotations_trainval2017.zip \
  http://images.cocodataset.org/annotations/annotations_trainval2017.zip

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

Keep the zip files until the extracted directories pass verification. They may
be removed afterward if space is needed.

## 5. Generate the 30k COCO baseline

Set the Hugging Face cache to the experiment storage:

```bash
export HF_HOME=$RAO/cache/huggingface
mkdir -p "$HF_HOME"
```

Run the existing four-column embedding pipeline:

```bash
cd "$RAO"
python coco_embed.py \
  --coco_root "$COCO" \
  --n_data 30000 \
  --n_query 2000 \
  --out "$RAO/embeddings/coco_30k_4col"
```

Verify every generated array:

```bash
python - <<'PY'
import json
import numpy as np
from pathlib import Path

p = Path("embeddings/coco_30k_4col")
cols = json.loads((p / "meta.json").read_text())["columns"]
for c in cols:
    d = np.load(p / f"data_{c}.npy")
    q = np.load(p / f"query_{c}.npy")
    print(c, d.shape, q.shape)
    assert d.shape[0] >= 30000
    assert d.shape[1] == 512
    assert q.shape[0] == 2000
PY
```

## 6. Run corrected FIR-MINT on COCO

Preserve the output directory from every campaign. Use a unique input folder
name so the script creates a unique result directory:

```bash
cd "$RAO"
python fir_mint_v4.py \
  --data "$RAO/embeddings/coco_30k_4col" \
  2>&1 | tee "$RAO/logs/coco_30k_4col.log"
```

Required checks:

- `results.md` exists.
- `results.json` exists.
- `fig1_measured.png` exists.
- `fig3_timelines.png` exists.
- E1 `Recall-violating mass` is zero for Static, FIR-MINT, and Full re-tune.
- E1 minimum recall is at least 0.90 for every policy and seed.
- E3 false re-tunes are zero in all scenarios.

Do not report latency or tuning claims if the recall checks fail.

## 7. Build six to eight real columns

The target real columns are:

1. CLIP image embedding.
2. DINOv2 image embedding.
3. CLIP caption embedding.
4. Sentence-transformer caption embedding.
5. Category text embedding.
6. Second caption embedding.
7. Optional image-caption joint embedding.
8. Optional alternative category/text embedding.

All columns must have the same dimension within one FIR-MINT input folder.
If models produce different dimensions, apply a documented fixed projection to
a common dimension before writing the arrays. Do not silently mix dimensions.

Use the same image IDs for data and query rows across every column. Use the
same train/validation split and the same held-out query IDs for all models.
Write a `meta.json` containing:

```json
{
  "columns": ["I_CLIP", "I_DINO", "T_CLIP", "T_ST", "M", "T2_CLIP"],
  "model_by_column": {},
  "data_ids": [],
  "query_ids": [],
  "projection": {}
}
```

Run FIR-MINT on the resulting folder and verify the same recall conditions.

## 8. Second dataset: Flickr30k

Download Flickr30k into:

```text
$RAO/data/flickr30k
```

Use the official dataset source and preserve its license/readme files. Create
the same six-column representation and the same file format as COCO:

```text
data_<column>.npy
query_<column>.npy
meta.json
```

The Flickr30k pipeline must record:

- Number of images and captions.
- Number of data rows and held-out queries.
- Image IDs used for each split.
- Model name and version for every column.
- Embedding dimension and normalization method.

Run:

```bash
cd "$RAO"
python fir_mint_v4.py \
  --data "$RAO/embeddings/flickr30k_6col" \
  2>&1 | tee "$RAO/logs/flickr30k_6col.log"
```

Apply the identical recall gates used for COCO.

## 9. Sensitivity analyses

Run each setting with a unique output folder and log:

### Monitoring window

Evaluate at least:

```text
150, 300, 600
```

### Drift threshold

Compare:

```text
bootstrap mean + 3 standard deviations
95th percentile bootstrap threshold
```

### Storage budget

Evaluate at least:

```text
4, 8, 12
```

### Recall target

Evaluate:

```text
0.90, 0.95, 0.99
```

Every sensitivity run must report:

- Mean and p95 workload latency.
- Minimum recall.
- Recall-violating mass.
- Retuning count.
- False-retuning count.
- What-if calls.
- Index builds.
- Tuning time.
- Index-build time.
- Detection delay.
- Switch-over time.

The code currently contains constants for several of these controls. Make
parameter changes explicit and record them in each output directory; do not
silently change the default baseline.

## 10. End-to-end adaptation timing

For every detector-driven retune, measure separately:

```text
detection delay
estimator/what-if time
configuration-search time
background index-build time
switch-over time
total adaptation time
```

Compare FIR+detector and Full+detector using the same workload windows and
hardware. Include index-build work in the total; do not report only estimator
calls as end-to-end speed.

## 11. Final result checklist

Before making claims, confirm:

- [ ] COCO has at least 30,000 data rows and 2,000 held-out queries.
- [ ] Flickr30k has been run with the same evaluation protocol.
- [ ] At least six real vector columns have been evaluated.
- [ ] Every reported policy meets recall target 0.90.
- [ ] Tie-aware recall is present in the copied `fir_mint_v4.py`.
- [ ] E1 and E3 raw JSON files are preserved.
- [ ] Every run has a log file.
- [ ] Sensitivity outputs have unique directories.
- [ ] GPU model, CUDA, Python, and package versions are recorded.
- [ ] No claim uses unmeasured operational time savings.

## 12. Current status

Completed locally:

- COCO Option B downloaded and embedded.
- Corrected tie-aware recall implementation.
- Corrected COCO E1/E3 rerun.
- Corrected baseline results and figures.

To run on the H100:

- Copy the corrected source files.
- Use `/data/$USER/RAO_NOV`.
- Create the GPU Python environment.
- Download COCO Option A there.
- Generate 30k COCO embeddings.
- Run the corrected four-column baseline.
- Generate the six-column multi-model dataset.
- Run Flickr30k and the sensitivity analyses.
