"""P1 data preparation: LAION 1M x 4-column table, held-out queries, and exact ground truth.

Columns (all 512-d, L2-normalised, float32 on disk):
  I_b32   image embedding released by LAION (OpenAI CLIP ViT-B/32)
  T_b32   caption embedding released by LAION (OpenAI CLIP ViT-B/32)
  T_b16   caption embedded here with openai/clip-vit-base-patch16
  T_lb32  caption embedded here with laion/CLIP-ViT-B-32-laion2B-s34B-b79K
Columns 3 and 4 are added by us (state this in the paper, brief Part 6.3).

Row filters, in order: NSFW tag == "UNLIKELY"; first occurrence of each caption; first
occurrence of each image embedding (exact fp16 bytes). Table = first N kept rows of
shards 0 then 1. Queries = Q rows drawn at random (seed 0) from the remaining kept rows.

Ground truth (brief rule 6.1.6): for every query type (column subset of size 1..3) and every
query row, the exact joint score mean_c(x_c . q_c) over all table rows, computed on GPU in
float32 without TF32. Stored: top-64 ids and scores, the k-th score (boundary) and the number
of rows within the v1.0 tie tolerance of the boundary (fir_mint_v4.recall_of).

Usage: python prep_laion.py --laion data/laion --out embeddings/laion_1m_4col [--n 1000000 --q 2000]
"""
import argparse, hashlib, itertools, json, time
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq
import torch
from transformers import CLIPModel, CLIPTokenizer

MODELS = {"T_b16": "openai/clip-vit-base-patch16", "T_lb32": "laion/CLIP-ViT-B-32-laion2B-s34B-b79K"}
TOP_K, KEEP, MAXQ = 10, 64, 3


def norm(x):
    return x / np.maximum(np.linalg.norm(x, axis=1, keepdims=True), 1e-12)


def select_rows(laion, shards):
    caps, keep, seen_cap, seen_img = [], [], set(), set()
    for s in shards:
        t = pq.read_table(laion / f"metadata_{s}.parquet", columns=["caption", "NSFW"])
        cap, nsfw = t.column("caption").to_pylist(), t.column("NSFW").to_pylist()
        img = np.load(laion / f"img_emb_{s}.npy", mmap_mode="r", allow_pickle=False)
        stats = {"rows": len(cap), "not_unlikely": 0, "dup_caption": 0, "dup_image": 0}
        for i, (c, n) in enumerate(zip(cap, nsfw)):
            if n != "UNLIKELY" or not (c or "").strip():
                stats["not_unlikely"] += 1; continue
            if c in seen_cap:
                stats["dup_caption"] += 1; continue
            h = hashlib.blake2b(np.asarray(img[i]).tobytes(), digest_size=16).digest()
            if h in seen_img:
                stats["dup_image"] += 1; continue
            seen_cap.add(c); seen_img.add(h); keep.append((s, i)); caps.append(c)
        print(f"shard {s}: {stats}", flush=True)
        yield s, stats
    select_rows.keep, select_rows.caps = keep, caps


def features(out):
    """Same extraction as code_frozen/embed_multi.py (transformers 5.x returns structured output)."""
    if torch.is_tensor(out):
        return out
    for attr in ("text_embeds", "pooler_output"):
        v = getattr(out, attr, None)
        if v is not None:
            return v
    raise TypeError(f"Unexpected CLIP feature output type: {type(out)}")


@torch.no_grad()
def embed_text(model_id, texts, dev, bs=2048):
    tok = CLIPTokenizer.from_pretrained(model_id)
    m = CLIPModel.from_pretrained(model_id, torch_dtype=torch.float16).to(dev).eval()
    out = np.empty((len(texts), 512), np.float32)
    for a in range(0, len(texts), bs):
        b = tok(texts[a:a + bs], padding=True, truncation=True, max_length=77, return_tensors="pt").to(dev)
        e = features(m.get_text_features(**b))
        out[a:a + bs] = torch.nn.functional.normalize(e.float(), dim=1).cpu().numpy()
        if a % (bs * 50) == 0:
            print(f"  {model_id}: {a}/{len(texts)}", flush=True)
    del m; torch.cuda.empty_cache()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--laion", default="data/laion"); ap.add_argument("--out", required=True)
    ap.add_argument("--n", type=int, default=1_000_000); ap.add_argument("--q", type=int, default=2000)
    a = ap.parse_args()
    t0 = time.time(); laion, out = Path(a.laion), Path(a.out); out.mkdir(parents=True, exist_ok=True)
    torch.backends.cuda.matmul.allow_tf32 = False; torch.backends.cudnn.allow_tf32 = False
    dev = "cuda"

    stats = dict(select_rows(laion, (0, 1)))
    keep, caps = select_rows.keep, select_rows.caps
    assert len(keep) >= a.n + a.q, f"only {len(keep)} rows after filtering"
    rest = np.random.default_rng(0).choice(np.arange(a.n, len(keep)), size=a.q, replace=False)
    sel = {"data": list(range(a.n)), "query": sorted(rest.tolist())}

    cols = {}
    for name, src in (("I_b32", "img_emb"), ("T_b32", "text_emb")):
        mm = {s: np.load(laion / f"{src}_{s}.npy", mmap_mode="r", allow_pickle=False) for s in (0, 1)}
        cols[name] = {part: norm(np.stack([mm[keep[j][0]][keep[j][1]] for j in idx]).astype(np.float32))
                      for part, idx in sel.items()}
    for name, mid in MODELS.items():
        for part, idx in sel.items():
            cols.setdefault(name, {})[part] = embed_text(mid, [caps[j] for j in idx], dev)
    names = ["I_b32", "T_b32", "T_b16", "T_lb32"]
    for n_ in names:
        np.save(out / f"data_{n_}.npy", cols[n_]["data"]); np.save(out / f"query_{n_}.npy", cols[n_]["query"])

    # ---------------- ground truth on GPU
    types = [q for m in range(1, MAXQ + 1) for q in itertools.combinations(range(len(names)), m)]
    X = [torch.from_numpy(cols[n_]["data"]).to(dev) for n_ in names]
    Q = [torch.from_numpy(cols[n_]["query"]).to(dev) for n_ in names]
    T, nq = len(types), a.q
    gt_ids = np.empty((T, nq, KEEP), np.int64); gt_sc = np.empty((T, nq, KEEP), np.float32)
    bnd = np.empty((T, nq), np.float32); nrel = np.empty((T, nq), np.int64)
    for b0 in range(0, nq, 200):
        S = [x @ q[b0:b0 + 200].T for x, q in zip(X, Q)]           # (N, B) per column
        for ti, ty in enumerate(types):
            s = sum(S[c] for c in ty) / len(ty)
            v, i = torch.topk(s, KEEP, dim=0)                         # (KEEP, B)
            kth = v[TOP_K - 1]
            tol = torch.clamp(kth.abs() * 1e-6, min=1e-6)
            nrel[ti, b0:b0 + 200] = (s >= kth - tol).sum(0).cpu().numpy()
            gt_ids[ti, b0:b0 + 200] = i.T.cpu().numpy(); gt_sc[ti, b0:b0 + 200] = v.T.cpu().numpy()
            bnd[ti, b0:b0 + 200] = kth.cpu().numpy()
        del S
    np.savez(out / "gt.npz", types=np.array([list(t) + [-1] * (MAXQ - len(t)) for t in types]),
             ids=gt_ids, scores=gt_sc, boundary=bnd, n_relevant=nrel)
    print("rows within tie tolerance: max", int(nrel.max()), "share > top-k", float((nrel > TOP_K).mean()), flush=True)

    meta = {"columns": names, "rows": a.n, "queries": a.q, "dim": 512,
            "sources": {"I_b32": "LAION-400M img_emb (OpenAI CLIP ViT-B/32), shards 0-1",
                        "T_b32": "LAION-400M text_emb (OpenAI CLIP ViT-B/32), shards 0-1",
                        **{k: f"caption embedded with {v} (added by us)" for k, v in MODELS.items()}},
            "filters": "NSFW == 'UNLIKELY'; first occurrence of caption; first occurrence of image embedding",
            "filter_stats": {str(k): v for k, v in stats.items()},
            "kept_rows_total": len(keep), "query_seed": 0,
            "licences": {"LAION metadata": "CC-BY 4.0", "models": "MIT"},
            "elapsed_s": time.time() - t0}
    json.dump(meta, open(out / "meta.json", "w"), indent=2)
    json.dump({p: [list(keep[j]) for j in idx] for p, idx in sel.items()}, open(out / "ids.json", "w"))
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
