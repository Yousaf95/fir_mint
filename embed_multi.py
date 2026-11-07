"""
Multi-model, multi-dataset embedding builder for FIR-MINT.

Builds one vector table where every row is one image and every column is one
(content, model) pair. All models output 512-d vectors, so every column has the same
dimension. All vectors are L2-normalized. Rows are sampled once (fixed seed) and the
same rows are used for every model; the chosen image ids are saved in ids.json.

Models (both 512-d):
  b32 = openai/clip-vit-base-patch32
  b16 = openai/clip-vit-base-patch16

Columns per model:
  COCO     : I (image), T (caption 1), M (object-category text), T2 (caption 2)
  Flickr30k: I (image), T (caption 1), T2 (caption 2), T3 (caption 3)
Column names are "<content>_<model>", e.g. I_b32, T_b16.

COCO layout (same as coco_embed.py):
  ROOT/train2017, ROOT/val2017, ROOT/annotations/{captions,instances}_{train,val}2017.json
  Data rows from train2017, query rows from val2017.

Flickr30k layout (Kaggle "flickr30k" style), one of:
  ROOT/flickr30k_images/*.jpg + ROOT/results.csv   (lines: image_name| comment_number| comment)
  ROOT/Images/*.jpg           + ROOT/captions.txt  (lines: image,caption)
  Data and query rows are a random disjoint split of all images.

Examples:
  python embed_multi.py --dataset coco   --root /data/coco      --models b32 b16 --n_data 30000 --n_query 2000 --out emb_coco_8col
  python embed_multi.py --dataset flickr --root /data/flickr30k --models b32     --n_data 28000 --n_query 2000 --out emb_flickr_4col
"""
import argparse, csv, json, random
from collections import defaultdict
from pathlib import Path
import numpy as np
import torch
from PIL import Image
from tqdm import tqdm
from transformers import CLIPModel, CLIPProcessor

MODELS = {"b32": "openai/clip-vit-base-patch32", "b16": "openai/clip-vit-base-patch16"}


# ---------------------------------------------------------------- dataset loaders
def coco_split(root, split):
    caps = json.load(open(root / "annotations" / f"captions_{split}.json", encoding="utf-8"))
    inst = json.load(open(root / "annotations" / f"instances_{split}.json", encoding="utf-8"))
    names = {c["id"]: c["name"] for c in inst["categories"]}
    captions, cats = defaultdict(list), defaultdict(set)
    for a in caps["annotations"]:
        captions[a["image_id"]].append(a["caption"].strip())
    for a in inst["annotations"]:
        cats[a["image_id"]].add(names[a["category_id"]])
    files = {im["id"]: str(root / split / im["file_name"]) for im in caps["images"]}
    rows = {}
    for i, f in files.items():
        if len(captions[i]) >= 2 and cats[i]:
            rows[f"{split}/{i}"] = {"path": f, "texts": {
                "T": captions[i][0], "T2": captions[i][1],
                "M": "a photo containing " + ", ".join(sorted(cats[i]))}}
    return rows


def load_coco(root, n_data, n_query, rng):
    tr, va = coco_split(root, "train2017"), coco_split(root, "val2017")
    d = rng.sample(sorted(tr), min(n_data, len(tr)))
    q = rng.sample(sorted(va), min(n_query, len(va)))
    return [tr[k] | {"id": k} for k in d], [va[k] | {"id": k} for k in q], ("I", "T", "M", "T2")


def load_flickr(root, n_data, n_query, rng):
    caps = defaultdict(list)
    if (root / "results.csv").exists():
        img_dir = root / "flickr30k_images"
        if (img_dir / "flickr30k_images").is_dir():
            img_dir = img_dir / "flickr30k_images"
        with open(root / "results.csv", encoding="utf-8") as f:
            next(f)
            for line in f:
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 3 and parts[2]:
                    caps[parts[0]].append(parts[2])
    elif (root / "captions.txt").exists():
        img_dir = root / "Images"
        with open(root / "captions.txt", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                caps[r["image"]].append(r["caption"].strip())
    else:
        raise FileNotFoundError("Flickr30k: expected results.csv or captions.txt in --root")
    rows = {k: {"id": k, "path": str(img_dir / k),
                "texts": {"T": v[0], "T2": v[1], "T3": v[2]}}
            for k, v in caps.items() if len(v) >= 3 and (img_dir / k).exists()}
    keys = sorted(rows)
    rng.shuffle(keys)
    n_query = min(n_query, len(keys) // 10)
    q, d = keys[:n_query], keys[n_query:n_query + n_data]
    return [rows[k] for k in d], [rows[k] for k in q], ("I", "T", "T2", "T3")


# ---------------------------------------------------------------- embedding
def as_tensor(out):
    """Transformers 4.x returns a tensor; 5.x may return a model-output object."""
    if torch.is_tensor(out):
        return out
    for attr in ("image_embeds", "text_embeds", "pooler_output"):
        v = getattr(out, attr, None)
        if v is not None:
            return v
    raise TypeError(f"Unexpected CLIP feature output type: {type(out)}")


@torch.no_grad()
def embed_rows(rows, contents, model, proc, device, bs):
    out = {c: [] for c in contents}
    for b in tqdm(range(0, len(rows), bs)):
        chunk = rows[b:b + bs]
        imgs = [Image.open(r["path"]).convert("RGB") for r in chunk]
        x = proc(images=imgs, return_tensors="pt").to(device)
        out["I"].append(as_tensor(model.get_image_features(**x)).float())
        for c in contents:
            if c == "I":
                continue
            t = proc(text=[r["texts"][c] for r in chunk], return_tensors="pt",
                     padding=True, truncation=True).to(device)
            out[c].append(as_tensor(model.get_text_features(**t)).float())
    return {c: torch.nn.functional.normalize(torch.cat(v), dim=-1).cpu().numpy().astype(np.float32)
            for c, v in out.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", choices=["coco", "flickr"], required=True)
    ap.add_argument("--root", required=True)
    ap.add_argument("--models", nargs="+", default=["b32"], choices=sorted(MODELS))
    ap.add_argument("--n_data", type=int, default=30000)
    ap.add_argument("--n_query", type=int, default=2000)
    ap.add_argument("--batch", type=int, default=64)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    root, out = Path(a.root), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    rng = random.Random(a.seed)
    data, query, contents = (load_coco if a.dataset == "coco" else load_flickr)(root, a.n_data, a.n_query, rng)
    json.dump({"data": [r["id"] for r in data], "query": [r["id"] for r in query]}, open(out / "ids.json", "w"))
    print(f"{a.dataset}: {len(data)} data rows, {len(query)} query rows, contents={contents}")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    columns = []
    for m in a.models:
        model = CLIPModel.from_pretrained(MODELS[m]).to(device).eval()
        proc = CLIPProcessor.from_pretrained(MODELS[m])
        for tag, rows in (("data", data), ("query", query)):
            vecs = embed_rows(rows, contents, model, proc, device, a.batch)
            for c in contents:
                np.save(out / f"{tag}_{c}_{m}.npy", vecs[c])
        columns += [f"{c}_{m}" for c in contents]
        del model
        if device == "cuda":
            torch.cuda.empty_cache()
        print(f"model {m} done")
    json.dump({"columns": columns, "dataset": a.dataset,
               "models": {m: MODELS[m] for m in a.models}, "seed": a.seed}, open(out / "meta.json", "w"), indent=1)
    for c in columns:
        print(c, np.load(out / f"data_{c}.npy").shape, np.load(out / f"query_{c}.npy").shape)


if __name__ == "__main__":
    main()
