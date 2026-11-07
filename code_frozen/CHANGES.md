# Frozen-code changes

- `coco_embed.py`: extract `pooler_output` from structured Transformers 5.x CLIP outputs; fixes the original embedding crash.
- `fir_mint_v4.py`: tie-aware recall uses a numerical boundary tolerance and the number of relevant slots; fixes false recall violations caused by floating-point ties.
- `fir_mint_v4.py`: merge calibration uses sampled minimum recall and pools through 2,560; prevents average-only calibration from selecting plans that fail individual queries.
- `fir_mint_v4.py`: duplicate-heavy single-column vectors use exact FAISS `IndexFlatIP`; fixes unreliable HNSW recall for repeated category-text vectors.
- `fir_mint_v4.py`: HNSW settings changed to M=32, efConstruction=128, efSearch=256; improves measured approximate recall on 30k-row data.
- `fir_mint_v4.py`: optional `FIR_BUILD_THREADS` controls index construction threads and resets FAISS to one thread after each build; query timing remains single-threaded.
- `fir_mint_v4.py`: real-data experiment constants and corrected recall implementation are frozen from the final COCO campaign.

## V3 (baselines campaign)
- Added `fir_baselines.py` (new file; imports frozen `fir_mint_v4.py`, no modification).

## V4 (extensions campaign)
- Added `fir_extensions.py` (new file; imports frozen `fir_mint_v4.py` and `fir_baselines.py`, no modification).
