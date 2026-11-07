"""
Build a real multi-vector table from MSCOCO 2017 with CLIP (ViT-B/32, 512-d).

Columns (one vector per image, all L2-normalized):
  0  I   image embedding
  1  T   embedding of caption #1
  2  M   embedding of the object-category text, e.g. "a photo containing dog, frisbee, person"
  3  T2  embedding of caption #2
Data rows come from train2017 (subsampled), query rows from val2017 (held out).

Setup (once):
  pip install torch transformers pillow numpy tqdm
  Download from https://cocodataset.org/#download :
    2017 Train images, 2017 Val images, 2017 Train/Val annotations
  Unzip so that you have:
    COCO_ROOT/train2017/*.jpg   COCO_ROOT/val2017/*.jpg
    COCO_ROOT/annotations/captions_train2017.json, instances_train2017.json (and *_val2017.json)

Run:
  python coco_embed.py --coco_root D:/coco --n_data 30000 --n_query 2000 --out coco_vectors
Lightweight option (only val2017 + annotations, ~1 GB; ~4000 data rows / 1000 queries):
  python coco_embed.py --coco_root D:/coco --val_only --out coco_vectors
Then:
  python fir_mint_v4.py --data coco_vectors
"""
import argparse, json, random
from collections import defaultdict
from pathlib import Path
import numpy as np
import torch
from PIL import Image
from tqdm import tqdm
from transformers import CLIPModel, CLIPProcessor

COLS = ("I", "T", "M", "T2")


def projected_features(output):
    return output.pooler_output if hasattr(output, "pooler_output") else output


def load_split(root, split):
    caps = json.load(open(root / "annotations" / f"captions_{split}.json", encoding="utf-8"))
    inst = json.load(open(root / "annotations" / f"instances_{split}.json", encoding="utf-8"))
    cat_name = {c["id"]: c["name"] for c in inst["categories"]}
    captions, cats = defaultdict(list), defaultdict(set)
    for a in caps["annotations"]:
        captions[a["image_id"]].append(a["caption"].strip())
    for a in inst["annotations"]:
        cats[a["image_id"]].add(cat_name[a["category_id"]])
    files = {im["id"]: im["file_name"] for im in caps["images"]}
    ids = [i for i in files if len(captions[i]) >= 2 and cats[i]]
    return ids, files, captions, cats


@torch.no_grad()
def embed(root, split, ids, files, captions, cats, model, proc, device, bs=64):
    out = {c: [] for c in COLS}
    for b in tqdm(range(0, len(ids), bs), desc=split):
        chunk = ids[b:b + bs]
        imgs = [Image.open(root / split / files[i]).convert("RGB") for i in chunk]
        x = proc(images=imgs, return_tensors="pt").to(device)
        out["I"].append(projected_features(model.get_image_features(**x)))
        for col, texts in (("T", [captions[i][0] for i in chunk]),
                           ("T2", [captions[i][1] for i in chunk]),
                           ("M", ["a photo containing " + ", ".join(sorted(cats[i])) for i in chunk])):
            t = proc(text=texts, return_tensors="pt", padding=True, truncation=True).to(device)
            out[col].append(projected_features(model.get_text_features(**t)))
    res = {}
    for c in COLS:
        v = torch.cat(out[c]).float()
        res[c] = torch.nn.functional.normalize(v, dim=-1).cpu().numpy().astype(np.float32)
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--coco_root", required=True)
    ap.add_argument("--n_data", type=int, default=30000)
    ap.add_argument("--n_query", type=int, default=2000)
    ap.add_argument("--out", default="coco_vectors")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--val_only", action="store_true",
                    help="use only val2017 (about 1 GB): split its images into data and query rows")
    a = ap.parse_args()
    root, out = Path(a.coco_root), Path(a.out)
    out.mkdir(exist_ok=True)
    random.seed(a.seed)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device).eval()
    proc = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

    if a.val_only:
        ids, files, caps, cats = load_split(root, "val2017")
        random.shuffle(ids)
        n_q = min(a.n_query, len(ids) // 5)
        jobs = [("val2017", ids[n_q:n_q + a.n_data], "data", (files, caps, cats)),
                ("val2017", ids[:n_q], "query", (files, caps, cats))]
    else:
        jobs = []
        for split, n, tag in (("train2017", a.n_data, "data"), ("val2017", a.n_query, "query")):
            ids, files, caps, cats = load_split(root, split)
            jobs.append((split, random.sample(ids, min(n, len(ids))), tag, (files, caps, cats)))
    for split, ids, tag, (files, caps, cats) in jobs:
        vecs = embed(root, split, ids, files, caps, cats, model, proc, device)
        for c in COLS:
            np.save(out / f"{tag}_{c}.npy", vecs[c])
        print(f"{tag}: {len(ids)} rows x {len(COLS)} columns x {vecs['I'].shape[1]} dims")
    json.dump({"columns": COLS, "model": "openai/clip-vit-base-patch32"}, open(out / "meta.json", "w"))


if __name__ == "__main__":
    main()
