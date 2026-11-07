"""
Create a vector folder that contains only some columns of an existing one
(e.g. a 6-column table from the 8-column table), in the format fir_mint_v4.py --data expects.

Usage:
  python make_subset.py --src emb_coco_8col --out emb_coco_6col --columns I_b32 T_b32 M_b32 T2_b32 I_b16 T_b16
"""
import argparse, json, shutil
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--src", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--columns", nargs="+", required=True)
a = ap.parse_args()
src, out = Path(a.src), Path(a.out)
out.mkdir(parents=True, exist_ok=True)
meta = json.load(open(src / "meta.json"))
missing = [c for c in a.columns if c not in meta["columns"]]
if missing:
    raise SystemExit(f"Columns not in {src}: {missing}. Available: {meta['columns']}")
for c in a.columns:
    for tag in ("data", "query"):
        shutil.copy2(src / f"{tag}_{c}.npy", out / f"{tag}_{c}.npy")
if (src / "ids.json").exists():
    shutil.copy2(src / "ids.json", out / "ids.json")
meta["columns"] = list(a.columns)
meta["subset_of"] = str(src)
json.dump(meta, open(out / "meta.json", "w"), indent=1)
print(f"Wrote {out} with {len(a.columns)} columns: {a.columns}")
