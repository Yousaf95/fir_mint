# Stage 1 trace of draft v1.0

Rows: 305; match: 291, MISMATCH: 4, info: 10, not traced: 0

| Place | Printed | Recomputed | Status | Source | Note |
|---|---:|---:|---|---|---|
| Table II COCO-4 (CPU host) Static | 2.647 | 2.6471 | match | `results/fir_mint_v4_results_coco_30k_4col/results.json` |  |
| Table II COCO-4 (CPU host) FIR-MINT | 1.999 | 1.9991 | match | `results/fir_mint_v4_results_coco_30k_4col/results.json` |  |
| Table II COCO-4 (CPU host) Full | 2.056 | 2.0562 | match | `results/fir_mint_v4_results_coco_30k_4col/results.json` |  |
| Table II COCO-4 (CPU host) FIR vs Static % | -19.2 | -19.2359 | match | `results/fir_mint_v4_results_coco_30k_4col/results.json` |  |
| Table II COCO-4 (CPU host) CI low | -49.5 | -49.4867 | match | `results/fir_mint_v4_results_coco_30k_4col/results.json` |  |
| Table II COCO-4 (CPU host) CI high | 11.0 | 11.0149 | match | `results/fir_mint_v4_results_coco_30k_4col/results.json` |  |
| Table II COCO-4 (CPU host) Min recall | 0.995 | 0.995 | match | `results/fir_mint_v4_results_coco_30k_4col/results.json` | per-seed FIR [0.998, 0.996, 0.988, 0.998, 0.996]; lowest over all policies and seeds 0.987 |
| Table II COCO-4 (H100 host) Static | 2.866 | 2.8661 | match | `fir_mint_v4_results_coco_30k_4col_gpu/results.json` |  |
| Table II COCO-4 (H100 host) FIR-MINT | 2.498 | 2.4978 | match | `fir_mint_v4_results_coco_30k_4col_gpu/results.json` |  |
| Table II COCO-4 (H100 host) Full | 2.417 | 2.4169 | match | `fir_mint_v4_results_coco_30k_4col_gpu/results.json` |  |
| Table II COCO-4 (H100 host) FIR vs Static % | -12.9 | -12.9226 | match | `fir_mint_v4_results_coco_30k_4col_gpu/results.json` |  |
| Table II COCO-4 (H100 host) CI low | -18.3 | -18.3384 | match | `fir_mint_v4_results_coco_30k_4col_gpu/results.json` |  |
| Table II COCO-4 (H100 host) CI high | -7.5 | -7.5068 | match | `fir_mint_v4_results_coco_30k_4col_gpu/results.json` |  |
| Table II COCO-4 (H100 host) Min recall | 0.995 | 0.9951 | match | `fir_mint_v4_results_coco_30k_4col_gpu/results.json` | per-seed FIR [0.998, 1.0, 0.983, 0.999, 0.996]; lowest over all policies and seeds 0.983 |
| Table II COCO-6 Static | 4.911 | 4.9105 | match | `FINAL_RESULTS/coco6/results.json` |  |
| Table II COCO-6 FIR-MINT | 4.211 | 4.211 | match | `FINAL_RESULTS/coco6/results.json` |  |
| Table II COCO-6 Full | 4.034 | 4.034 | match | `FINAL_RESULTS/coco6/results.json` |  |
| Table II COCO-6 FIR vs Static % | -13.2 | -13.1863 | match | `FINAL_RESULTS/coco6/results.json` |  |
| Table II COCO-6 CI low | -29.3 | -29.3326 | match | `FINAL_RESULTS/coco6/results.json` |  |
| Table II COCO-6 CI high | 3.0 | 2.96 | match | `FINAL_RESULTS/coco6/results.json` |  |
| Table II COCO-6 Min recall | 0.969 | 0.9692 | match | `FINAL_RESULTS/coco6/results.json` | per-seed FIR [0.933, 0.989, 0.925, 0.999, 0.999]; lowest over all policies and seeds 0.850 |
| Table II Flickr30k-4 Static | 1.789 | 1.7889 | match | `FINAL_RESULTS/flickr4/results.json` |  |
| Table II Flickr30k-4 FIR-MINT | 1.494 | 1.4936 | match | `FINAL_RESULTS/flickr4/results.json` |  |
| Table II Flickr30k-4 Full | 1.481 | 1.4807 | match | `FINAL_RESULTS/flickr4/results.json` |  |
| Table II Flickr30k-4 FIR vs Static % | -14.9 | -14.9357 | match | `FINAL_RESULTS/flickr4/results.json` |  |
| Table II Flickr30k-4 CI low | -29.6 | -29.5597 | match | `FINAL_RESULTS/flickr4/results.json` |  |
| Table II Flickr30k-4 CI high | -0.3 | -0.3117 | match | `FINAL_RESULTS/flickr4/results.json` |  |
| Table II Flickr30k-4 Min recall | 0.993 | 0.9928 | match | `FINAL_RESULTS/flickr4/results.json` | per-seed FIR [0.993, 0.994, 0.998, 0.988, 0.992]; lowest over all policies and seeds 0.988 |
| VII-A Flickr30k p95 FIR vs Static % | -21.6 | -21.6181 | match | `FINAL_RESULTS/flickr4/results.json` |  |
| Table II Synthetic-4 Static | 0.633 | 0.6336 | MISMATCH | `runs/synthetic/fir_mint_v4_results/results.json` |  |
| Table II Synthetic-4 FIR-MINT | 0.517 | 0.5168 | match | `runs/synthetic/fir_mint_v4_results/results.json` |  |
| Table II Synthetic-4 Full | 0.516 | 0.5164 | match | `runs/synthetic/fir_mint_v4_results/results.json` |  |
| Table II Synthetic-4 FIR vs Static % | -18.3 | -18.275 | match | `runs/synthetic/fir_mint_v4_results/results.json` |  |
| Table II Synthetic-4 CI low | -28.4 | -28.3653 | match | `runs/synthetic/fir_mint_v4_results/results.json` |  |
| Table II Synthetic-4 CI high | -8.2 | -8.1847 | match | `runs/synthetic/fir_mint_v4_results/results.json` |  |
| Table II Synthetic-4 Min recall | None | 0.9965 | info | `runs/synthetic/fir_mint_v4_results/results.json` | per-seed FIR [0.989, 0.999, 1.0, 0.995, 1.0]; lowest over all policies and seeds 0.987 |
| VII-A FIR vs Full measured % (low end) | -3.0 | -3.049 | match | `E1 files` |  |
| VII-A FIR vs Full measured % (high end) | 5.1 | 5.0725 | match | `E1 files` |  |
| Table III COCO-4 (CPU host) abrupt | -13.3 | -13.2599 | match | `results/fir_mint_v4_results_coco_30k_4col/results.json` |  |
| Table III COCO-4 (CPU host) abrupt CI low | -24.5 | -24.4511 | match | `results/fir_mint_v4_results_coco_30k_4col/results.json` |  |
| Table III COCO-4 (CPU host) abrupt CI high | -2.1 | -2.0687 | match | `results/fir_mint_v4_results_coco_30k_4col/results.json` |  |
| Table III COCO-4 (CPU host) gradual | -18.0 | -17.9876 | match | `results/fir_mint_v4_results_coco_30k_4col/results.json` |  |
| Table III COCO-4 (CPU host) gradual CI low | -23.7 | -23.716 | match | `results/fir_mint_v4_results_coco_30k_4col/results.json` |  |
| Table III COCO-4 (CPU host) gradual CI high | -12.3 | -12.2592 | match | `results/fir_mint_v4_results_coco_30k_4col/results.json` |  |
| Table III COCO-4 (CPU host) recurring | -9.4 | -9.4202 | match | `results/fir_mint_v4_results_coco_30k_4col/results.json` |  |
| Table III COCO-4 (CPU host) recurring CI low | -18.6 | -18.6477 | match | `results/fir_mint_v4_results_coco_30k_4col/results.json` |  |
| Table III COCO-4 (CPU host) recurring CI high | -0.2 | -0.1926 | match | `results/fir_mint_v4_results_coco_30k_4col/results.json` |  |
| Table III COCO-4 (CPU host) new_type | -28.1 | -28.1153 | match | `results/fir_mint_v4_results_coco_30k_4col/results.json` |  |
| Table III COCO-4 (CPU host) new_type CI low | -49.4 | -49.3924 | match | `results/fir_mint_v4_results_coco_30k_4col/results.json` |  |
| Table III COCO-4 (CPU host) new_type CI high | -6.8 | -6.8381 | match | `results/fir_mint_v4_results_coco_30k_4col/results.json` |  |
| Table III COCO-4 (H100 host) abrupt | -5.9 | -5.8587 | match | `fir_mint_v4_results_coco_30k_4col_gpu/results.json` |  |
| Table III COCO-4 (H100 host) abrupt CI low | -13.2 | -13.19 | match | `fir_mint_v4_results_coco_30k_4col_gpu/results.json` |  |
| Table III COCO-4 (H100 host) abrupt CI high | 1.5 | 1.4726 | match | `fir_mint_v4_results_coco_30k_4col_gpu/results.json` |  |
| Table III COCO-4 (H100 host) gradual | -13.4 | -13.4051 | match | `fir_mint_v4_results_coco_30k_4col_gpu/results.json` |  |
| Table III COCO-4 (H100 host) gradual CI low | -28.7 | -28.678 | match | `fir_mint_v4_results_coco_30k_4col_gpu/results.json` |  |
| Table III COCO-4 (H100 host) gradual CI high | 1.9 | 1.8677 | match | `fir_mint_v4_results_coco_30k_4col_gpu/results.json` |  |
| Table III COCO-4 (H100 host) recurring | -6.1 | -6.1328 | match | `fir_mint_v4_results_coco_30k_4col_gpu/results.json` |  |
| Table III COCO-4 (H100 host) recurring CI low | -15.0 | -15.0026 | match | `fir_mint_v4_results_coco_30k_4col_gpu/results.json` |  |
| Table III COCO-4 (H100 host) recurring CI high | 2.7 | 2.7371 | match | `fir_mint_v4_results_coco_30k_4col_gpu/results.json` |  |
| Table III COCO-4 (H100 host) new_type | -34.4 | -34.354 | match | `fir_mint_v4_results_coco_30k_4col_gpu/results.json` |  |
| Table III COCO-4 (H100 host) new_type CI low | -66.8 | -66.7679 | match | `fir_mint_v4_results_coco_30k_4col_gpu/results.json` |  |
| Table III COCO-4 (H100 host) new_type CI high | -1.9 | -1.9402 | match | `fir_mint_v4_results_coco_30k_4col_gpu/results.json` |  |
| Table III COCO-6 abrupt | -21.6 | -21.6333 | match | `FINAL_RESULTS/coco6/results.json` |  |
| Table III COCO-6 abrupt CI low | -30.8 | -30.803 | match | `FINAL_RESULTS/coco6/results.json` |  |
| Table III COCO-6 abrupt CI high | -12.5 | -12.4636 | match | `FINAL_RESULTS/coco6/results.json` |  |
| Table III COCO-6 gradual | -17.8 | -17.8082 | match | `FINAL_RESULTS/coco6/results.json` |  |
| Table III COCO-6 gradual CI low | -29.6 | -29.5686 | match | `FINAL_RESULTS/coco6/results.json` |  |
| Table III COCO-6 gradual CI high | -6.0 | -6.0477 | match | `FINAL_RESULTS/coco6/results.json` |  |
| Table III COCO-6 recurring | -11.1 | -11.1344 | match | `FINAL_RESULTS/coco6/results.json` |  |
| Table III COCO-6 recurring CI low | -20.1 | -20.1346 | match | `FINAL_RESULTS/coco6/results.json` |  |
| Table III COCO-6 recurring CI high | -2.1 | -2.1341 | match | `FINAL_RESULTS/coco6/results.json` |  |
| Table III COCO-6 new_type | -30.9 | -30.9384 | match | `FINAL_RESULTS/coco6/results.json` |  |
| Table III COCO-6 new_type CI low | -56.7 | -56.7488 | match | `FINAL_RESULTS/coco6/results.json` |  |
| Table III COCO-6 new_type CI high | -5.1 | -5.1281 | match | `FINAL_RESULTS/coco6/results.json` |  |
| Table III Flickr30k-4 abrupt | -7.4 | -7.351 | match | `FINAL_RESULTS/flickr4/results.json` |  |
| Table III Flickr30k-4 abrupt CI low | -10.6 | -10.6149 | match | `FINAL_RESULTS/flickr4/results.json` |  |
| Table III Flickr30k-4 abrupt CI high | -4.1 | -4.0871 | match | `FINAL_RESULTS/flickr4/results.json` |  |
| Table III Flickr30k-4 gradual | -4.8 | -4.803 | match | `FINAL_RESULTS/flickr4/results.json` |  |
| Table III Flickr30k-4 gradual CI low | -9.3 | -9.3024 | match | `FINAL_RESULTS/flickr4/results.json` |  |
| Table III Flickr30k-4 gradual CI high | -0.3 | -0.3036 | match | `FINAL_RESULTS/flickr4/results.json` |  |
| Table III Flickr30k-4 recurring | -2.7 | -2.6638 | match | `FINAL_RESULTS/flickr4/results.json` |  |
| Table III Flickr30k-4 recurring CI low | -5.5 | -5.4808 | match | `FINAL_RESULTS/flickr4/results.json` |  |
| Table III Flickr30k-4 recurring CI high | 0.2 | 0.1533 | match | `FINAL_RESULTS/flickr4/results.json` |  |
| Table III Flickr30k-4 new_type | -11.9 | -11.9094 | match | `FINAL_RESULTS/flickr4/results.json` |  |
| Table III Flickr30k-4 new_type CI low | -20.8 | -20.8067 | match | `FINAL_RESULTS/flickr4/results.json` |  |
| Table III Flickr30k-4 new_type CI high | -3.0 | -3.0122 | match | `FINAL_RESULTS/flickr4/results.json` |  |
| Table III Synthetic-5 (printed) / Synthetic-4 (file) abrupt | -23.1 | -23.1142 | match | `runs/synthetic/fir_mint_v4_results/results.json` |  |
| Table III Synthetic-5 (printed) / Synthetic-4 (file) abrupt CI low | -32.3 | -32.308 | match | `runs/synthetic/fir_mint_v4_results/results.json` |  |
| Table III Synthetic-5 (printed) / Synthetic-4 (file) abrupt CI high | -13.9 | -13.9205 | match | `runs/synthetic/fir_mint_v4_results/results.json` |  |
| Table III Synthetic-5 (printed) / Synthetic-4 (file) gradual | -16.5 | -16.4509 | match | `runs/synthetic/fir_mint_v4_results/results.json` |  |
| Table III Synthetic-5 (printed) / Synthetic-4 (file) gradual CI low | -25.2 | -25.2313 | match | `runs/synthetic/fir_mint_v4_results/results.json` |  |
| Table III Synthetic-5 (printed) / Synthetic-4 (file) gradual CI high | -7.7 | -7.6704 | match | `runs/synthetic/fir_mint_v4_results/results.json` |  |
| Table III Synthetic-5 (printed) / Synthetic-4 (file) recurring | -15.9 | -15.9336 | match | `runs/synthetic/fir_mint_v4_results/results.json` |  |
| Table III Synthetic-5 (printed) / Synthetic-4 (file) recurring CI low | -19.3 | -19.2724 | match | `runs/synthetic/fir_mint_v4_results/results.json` |  |
| Table III Synthetic-5 (printed) / Synthetic-4 (file) recurring CI high | -12.6 | -12.5948 | match | `runs/synthetic/fir_mint_v4_results/results.json` |  |
| Table III Synthetic-5 (printed) / Synthetic-4 (file) new_type | -32.3 | -32.338 | match | `runs/synthetic/fir_mint_v4_results/results.json` |  |
| Table III Synthetic-5 (printed) / Synthetic-4 (file) new_type CI low | -41.0 | -40.9921 | match | `runs/synthetic/fir_mint_v4_results/results.json` |  |
| Table III Synthetic-5 (printed) / Synthetic-4 (file) new_type CI high | -23.7 | -23.6838 | match | `runs/synthetic/fir_mint_v4_results/results.json` |  |
| VII-B gains new type 12-34% (low end) | 12 | 11.9 | match | `Table III` |  |
| VII-B gains new type 12-34% (high end) | 34 | 34.4 | match | `Table III` |  |
| VII-B false re-tunes (all E3 FIR+detector runs) | 0 | 0 | match | `E3 files` |  |
| VII-B mean delay (windows), per dataset over 4 scenarios (low end) | 1.4 | 1.4 | match | `E3 files` |  |
| VII-B mean delay (windows), per dataset over 4 scenarios (high end) | 1.45 | 1.45 | match | `E3 files` |  |
| VII-B max delay (windows) | 4 | 4 | match | `E3 files` |  |
| VII-C FIR vs Full+detector % (low end) | -2.3 | -2.2551 | match | `E3 files` |  |
| VII-C FIR vs Full+detector % (high end) | 1.0 | 0.9802 | match | `E3 files` |  |
| VII-C what-if ratio Full-every-window/FIR (low end) | 8 | 7.5345 | match | `E3 files` |  |
| VII-C what-if ratio Full-every-window/FIR (high end) | 27 | 27.4787 | match | `E3 files` |  |
| VII-C build ratio low end | 3.6 | 3.5926 | match | `E3 files` |  |
| VII-C build ratio high end | 30 | 30.2 | match | `E3 files` |  |
| VII-C cost vs every-window % (low end) | -2 | -1.9302 | match | `E3 files` |  |
| VII-C cost vs every-window % (high end) | 6 | 5.7119 | match | `E3 files` |  |
| Table IV Flickr30k-4 abrupt Static | 10.8 | 10.8387 | match | `FINAL_RESULTS/baselines/flickr4/baselines.json` |  |
| Table IV Flickr30k-4 abrupt Robust static | 12.9 | 12.936 | match | `FINAL_RESULTS/baselines/flickr4/baselines.json` |  |
| Table IV Flickr30k-4 abrupt FIR-MINT | 0.5 | 0.5342 | match | `FINAL_RESULTS/baselines/flickr4/baselines.json` |  |
| Table IV Flickr30k-4 abrupt Full | 1.2 | 1.2411 | match | `FINAL_RESULTS/baselines/flickr4/baselines.json` |  |
| Table IV Flickr30k-4 abrupt Capped full | 1.2 | 1.2411 | match | `FINAL_RESULTS/baselines/flickr4/baselines.json` |  |
| Table IV Flickr30k-4 abrupt Cost trigger | 0.5 | 0.5342 | match | `FINAL_RESULTS/baselines/flickr4/baselines.json` |  |
| Table IV Flickr30k-4 abrupt Forecast | 0.7 | 0.7443 | match | `FINAL_RESULTS/baselines/flickr4/baselines.json` |  |
| Table IV Flickr30k-4 abrupt Continuous | -0.1 | -0.0693 | match | `FINAL_RESULTS/baselines/flickr4/baselines.json` |  |
| Table IV Flickr30k-4 gradual Static | 8.1 | 8.0948 | match | `FINAL_RESULTS/baselines/flickr4/baselines.json` |  |
| Table IV Flickr30k-4 gradual Robust static | 6.8 | 6.7928 | match | `FINAL_RESULTS/baselines/flickr4/baselines.json` |  |
| Table IV Flickr30k-4 gradual FIR-MINT | 0.6 | 0.5562 | match | `FINAL_RESULTS/baselines/flickr4/baselines.json` |  |
| Table IV Flickr30k-4 gradual Full | 1.6 | 1.6039 | match | `FINAL_RESULTS/baselines/flickr4/baselines.json` |  |
| Table IV Flickr30k-4 gradual Capped full | 1.9 | 1.9418 | match | `FINAL_RESULTS/baselines/flickr4/baselines.json` |  |
| Table IV Flickr30k-4 gradual Cost trigger | 0.7 | 0.7064 | match | `FINAL_RESULTS/baselines/flickr4/baselines.json` |  |
| Table IV Flickr30k-4 gradual Forecast | 0.6 | 0.6195 | match | `FINAL_RESULTS/baselines/flickr4/baselines.json` |  |
| Table IV Flickr30k-4 gradual Continuous | -0.1 | -0.0537 | match | `FINAL_RESULTS/baselines/flickr4/baselines.json` |  |
| Table IV Flickr30k-4 recurring Static | 11.5 | 11.5141 | match | `FINAL_RESULTS/baselines/flickr4/baselines.json` |  |
| Table IV Flickr30k-4 recurring Robust static | 12.4 | 12.3636 | match | `FINAL_RESULTS/baselines/flickr4/baselines.json` |  |
| Table IV Flickr30k-4 recurring FIR-MINT | 3.5 | 3.5114 | match | `FINAL_RESULTS/baselines/flickr4/baselines.json` |  |
| Table IV Flickr30k-4 recurring Full | 3.8 | 3.7594 | match | `FINAL_RESULTS/baselines/flickr4/baselines.json` |  |
| Table IV Flickr30k-4 recurring Capped full | 3.8 | 3.7594 | match | `FINAL_RESULTS/baselines/flickr4/baselines.json` |  |
| Table IV Flickr30k-4 recurring Cost trigger | 2.6 | 2.6003 | match | `FINAL_RESULTS/baselines/flickr4/baselines.json` |  |
| Table IV Flickr30k-4 recurring Forecast | 5.2 | 5.1766 | match | `FINAL_RESULTS/baselines/flickr4/baselines.json` |  |
| Table IV Flickr30k-4 recurring Continuous | 1.8 | 1.7882 | match | `FINAL_RESULTS/baselines/flickr4/baselines.json` |  |
| Table IV Flickr30k-4 new_type Static | 21.0 | 21.0319 | match | `FINAL_RESULTS/baselines/flickr4/baselines.json` |  |
| Table IV Flickr30k-4 new_type Robust static | 22.7 | 22.6521 | match | `FINAL_RESULTS/baselines/flickr4/baselines.json` |  |
| Table IV Flickr30k-4 new_type FIR-MINT | 2.2 | 2.2283 | match | `FINAL_RESULTS/baselines/flickr4/baselines.json` |  |
| Table IV Flickr30k-4 new_type Full | 2.3 | 2.2636 | match | `FINAL_RESULTS/baselines/flickr4/baselines.json` |  |
| Table IV Flickr30k-4 new_type Capped full | 2.3 | 2.3419 | match | `FINAL_RESULTS/baselines/flickr4/baselines.json` |  |
| Table IV Flickr30k-4 new_type Cost trigger | 2.2 | 2.2283 | match | `FINAL_RESULTS/baselines/flickr4/baselines.json` |  |
| Table IV Flickr30k-4 new_type Forecast | 2.8 | 2.8183 | match | `FINAL_RESULTS/baselines/flickr4/baselines.json` |  |
| Table IV Flickr30k-4 new_type Continuous | 1.3 | 1.2715 | match | `FINAL_RESULTS/baselines/flickr4/baselines.json` |  |
| Table IV COCO-4 abrupt Static | 47.7 | 47.6625 | match | `FINAL_RESULTS/baselines/coco4/baselines.json` |  |
| Table IV COCO-4 abrupt Robust static | 19.3 | 19.259 | match | `FINAL_RESULTS/baselines/coco4/baselines.json` |  |
| Table IV COCO-4 abrupt FIR-MINT | 5.7 | 5.7225 | match | `FINAL_RESULTS/baselines/coco4/baselines.json` |  |
| Table IV COCO-4 abrupt Full | 6.0 | 6.0137 | match | `FINAL_RESULTS/baselines/coco4/baselines.json` |  |
| Table IV COCO-4 abrupt Capped full | 6.0 | 6.0137 | match | `FINAL_RESULTS/baselines/coco4/baselines.json` |  |
| Table IV COCO-4 abrupt Cost trigger | 10.5 | 10.5059 | match | `FINAL_RESULTS/baselines/coco4/baselines.json` |  |
| Table IV COCO-4 abrupt Forecast | 6.6 | 6.5661 | match | `FINAL_RESULTS/baselines/coco4/baselines.json` |  |
| Table IV COCO-4 abrupt Continuous | 3.5 | 3.4865 | match | `FINAL_RESULTS/baselines/coco4/baselines.json` |  |
| Table IV COCO-4 gradual Static | 31.2 | 31.1823 | match | `FINAL_RESULTS/baselines/coco4/baselines.json` |  |
| Table IV COCO-4 gradual Robust static | 34.5 | 34.465 | match | `FINAL_RESULTS/baselines/coco4/baselines.json` |  |
| Table IV COCO-4 gradual FIR-MINT | 2.6 | 2.636 | match | `FINAL_RESULTS/baselines/coco4/baselines.json` |  |
| Table IV COCO-4 gradual Full | 2.6 | 2.636 | match | `FINAL_RESULTS/baselines/coco4/baselines.json` |  |
| Table IV COCO-4 gradual Capped full | 2.6 | 2.636 | match | `FINAL_RESULTS/baselines/coco4/baselines.json` |  |
| Table IV COCO-4 gradual Cost trigger | 5.4 | 5.4075 | match | `FINAL_RESULTS/baselines/coco4/baselines.json` |  |
| Table IV COCO-4 gradual Forecast | 1.5 | 1.5336 | match | `FINAL_RESULTS/baselines/coco4/baselines.json` |  |
| Table IV COCO-4 gradual Continuous | 1.1 | 1.0722 | match | `FINAL_RESULTS/baselines/coco4/baselines.json` |  |
| Table IV COCO-4 recurring Static | 40.5 | 40.476 | match | `FINAL_RESULTS/baselines/coco4/baselines.json` |  |
| Table IV COCO-4 recurring Robust static | 38.6 | 38.5607 | match | `FINAL_RESULTS/baselines/coco4/baselines.json` |  |
| Table IV COCO-4 recurring FIR-MINT | 7.9 | 7.8937 | match | `FINAL_RESULTS/baselines/coco4/baselines.json` |  |
| Table IV COCO-4 recurring Full | 9.5 | 9.5286 | match | `FINAL_RESULTS/baselines/coco4/baselines.json` |  |
| Table IV COCO-4 recurring Capped full | 9.5 | 9.5286 | match | `FINAL_RESULTS/baselines/coco4/baselines.json` |  |
| Table IV COCO-4 recurring Cost trigger | 10.6 | 10.6284 | match | `FINAL_RESULTS/baselines/coco4/baselines.json` |  |
| Table IV COCO-4 recurring Forecast | 19.5 | 19.501 | match | `FINAL_RESULTS/baselines/coco4/baselines.json` |  |
| Table IV COCO-4 recurring Continuous | 6.1 | 6.0796 | match | `FINAL_RESULTS/baselines/coco4/baselines.json` |  |
| Table IV COCO-4 new_type Static | 59.5 | 59.4874 | match | `FINAL_RESULTS/baselines/coco4/baselines.json` |  |
| Table IV COCO-4 new_type Robust static | 60.5 | 60.497 | match | `FINAL_RESULTS/baselines/coco4/baselines.json` |  |
| Table IV COCO-4 new_type FIR-MINT | 6.8 | 6.7744 | match | `FINAL_RESULTS/baselines/coco4/baselines.json` |  |
| Table IV COCO-4 new_type Full | 7.1 | 7.1003 | match | `FINAL_RESULTS/baselines/coco4/baselines.json` |  |
| Table IV COCO-4 new_type Capped full | 7.1 | 7.1003 | match | `FINAL_RESULTS/baselines/coco4/baselines.json` |  |
| Table IV COCO-4 new_type Cost trigger | 6.8 | 6.7913 | match | `FINAL_RESULTS/baselines/coco4/baselines.json` |  |
| Table IV COCO-4 new_type Forecast | 8.3 | 8.2513 | match | `FINAL_RESULTS/baselines/coco4/baselines.json` |  |
| Table IV COCO-4 new_type Continuous | 3.8 | 3.7869 | match | `FINAL_RESULTS/baselines/coco4/baselines.json` |  |
| Table IV COCO-6 abrupt Static | 24.9 | 24.9408 | match | `FINAL_RESULTS/baselines/coco6/baselines.json` |  |
| Table IV COCO-6 abrupt Robust static | 30.2 | 30.2409 | match | `FINAL_RESULTS/baselines/coco6/baselines.json` |  |
| Table IV COCO-6 abrupt FIR-MINT | 0.1 | 0.1276 | match | `FINAL_RESULTS/baselines/coco6/baselines.json` |  |
| Table IV COCO-6 abrupt Full | 2.8 | 2.7575 | match | `FINAL_RESULTS/baselines/coco6/baselines.json` |  |
| Table IV COCO-6 abrupt Capped full | 5.3 | 5.2506 | match | `FINAL_RESULTS/baselines/coco6/baselines.json` |  |
| Table IV COCO-6 abrupt Cost trigger | 2.7 | 2.7127 | match | `FINAL_RESULTS/baselines/coco6/baselines.json` |  |
| Table IV COCO-6 abrupt Forecast | 1.6 | 1.5645 | match | `FINAL_RESULTS/baselines/coco6/baselines.json` |  |
| Table IV COCO-6 abrupt Continuous | 0.2 | 0.2169 | match | `FINAL_RESULTS/baselines/coco6/baselines.json` |  |
| Table IV COCO-6 gradual Static | 38.7 | 38.6735 | match | `FINAL_RESULTS/baselines/coco6/baselines.json` |  |
| Table IV COCO-6 gradual Robust static | 30.5 | 30.4553 | match | `FINAL_RESULTS/baselines/coco6/baselines.json` |  |
| Table IV COCO-6 gradual FIR-MINT | 1.0 | 0.9545 | match | `FINAL_RESULTS/baselines/coco6/baselines.json` |  |
| Table IV COCO-6 gradual Full | 2.4 | 2.3537 | match | `FINAL_RESULTS/baselines/coco6/baselines.json` |  |
| Table IV COCO-6 gradual Capped full | 2.9 | 2.9011 | match | `FINAL_RESULTS/baselines/coco6/baselines.json` |  |
| Table IV COCO-6 gradual Cost trigger | 3.5 | 3.4826 | match | `FINAL_RESULTS/baselines/coco6/baselines.json` |  |
| Table IV COCO-6 gradual Forecast | 1.7 | 1.7189 | match | `FINAL_RESULTS/baselines/coco6/baselines.json` |  |
| Table IV COCO-6 gradual Continuous | -0.2 | -0.2484 | match | `FINAL_RESULTS/baselines/coco6/baselines.json` |  |
| Table IV COCO-6 recurring Static | 38.6 | 38.5548 | match | `FINAL_RESULTS/baselines/coco6/baselines.json` |  |
| Table IV COCO-6 recurring Robust static | 31.5 | 31.4849 | match | `FINAL_RESULTS/baselines/coco6/baselines.json` |  |
| Table IV COCO-6 recurring FIR-MINT | 12.2 | 12.2314 | match | `FINAL_RESULTS/baselines/coco6/baselines.json` |  |
| Table IV COCO-6 recurring Full | 12.4 | 12.3545 | match | `FINAL_RESULTS/baselines/coco6/baselines.json` |  |
| Table IV COCO-6 recurring Capped full | 18.1 | 18.1479 | match | `FINAL_RESULTS/baselines/coco6/baselines.json` |  |
| Table IV COCO-6 recurring Cost trigger | 12.9 | 12.9405 | match | `FINAL_RESULTS/baselines/coco6/baselines.json` |  |
| Table IV COCO-6 recurring Forecast | 12.9 | 12.8621 | match | `FINAL_RESULTS/baselines/coco6/baselines.json` |  |
| Table IV COCO-6 recurring Continuous | 6.2 | 6.2396 | match | `FINAL_RESULTS/baselines/coco6/baselines.json` |  |
| Table IV COCO-6 new_type Static | 151.3 | 151.2731 | match | `FINAL_RESULTS/baselines/coco6/baselines.json` |  |
| Table IV COCO-6 new_type Robust static | 132.1 | 132.0503 | match | `FINAL_RESULTS/baselines/coco6/baselines.json` |  |
| Table IV COCO-6 new_type FIR-MINT | 17.1 | 17.0933 | match | `FINAL_RESULTS/baselines/coco6/baselines.json` |  |
| Table IV COCO-6 new_type Full | 16.2 | 16.1998 | match | `FINAL_RESULTS/baselines/coco6/baselines.json` |  |
| Table IV COCO-6 new_type Capped full | 16.8 | 16.8101 | match | `FINAL_RESULTS/baselines/coco6/baselines.json` |  |
| Table IV COCO-6 new_type Cost trigger | 20.3 | 20.3335 | match | `FINAL_RESULTS/baselines/coco6/baselines.json` |  |
| Table IV COCO-6 new_type Forecast | 17.3 | 17.2508 | match | `FINAL_RESULTS/baselines/coco6/baselines.json` |  |
| Table IV COCO-6 new_type Continuous | 8.7 | 8.7466 | match | `FINAL_RESULTS/baselines/coco6/baselines.json` |  |
| Table IV caption: Continuous reconfigurations before drift (low end) | 5.6 | 5.6 | match | `baselines files` |  |
| Table IV caption: Continuous reconfigurations before drift (high end) | 9.2 | 9.2 | match | `baselines files` |  |
| Table IV caption / abstract: what-if ratio Continuous/FIR (low end) | 8 | 7.5822 | match | `baselines files` |  |
| Table IV caption / abstract: what-if ratio Continuous/FIR (high end) | 29 | 28.6761 | match | `baselines files` |  |
| Table IV caption: build ratio Continuous/FIR (low end) | 3 | 3.2632 | match | `baselines files` |  |
| Table IV caption: build ratio Continuous/FIR (high end) | 20 | 20.4286 | match | `baselines files` |  |
| VII-D robust static above hindsight % (low end) | 7 | 6.7928 | match | `baselines files` |  |
| VII-D robust static above hindsight % (high end) | 132 | 132.0503 | match | `baselines files` |  |
| VII-D FIR within 8% of hindsight (of 16 pairs) | 14 | 14 | match | `baselines files` |  |
| VII-D Continuous buys points (low end) | 1 | -0.0892 | MISMATCH | `baselines files` |  |
| VII-D Continuous buys points (high end) | 9 | 8.3467 | MISMATCH | `baselines files` |  |
| VII-D FIR <= Full (of 16 pairs) | 13 | 13 | match | `baselines files` |  |
| VII-D FIR worse than Full by at most (points) | 0.9 | 0.8935 | match | `baselines files` |  |
| VII-D cost trigger worse on COCO-4 by up to (points) | 4.8 | 4.7835 | match | `baselines coco4` |  |
| VII-D COCO-4 what-if calls cost trigger (low end) | 20 | 20.4 | match | `FINAL_RESULTS/baselines/coco4/baselines.json` |  |
| VII-D COCO-4 what-if calls cost trigger (high end) | 44 | 44.4 | match | `FINAL_RESULTS/baselines/coco4/baselines.json` |  |
| VII-D COCO-4 what-if calls FIR (low end) | 49 | 49.4 | match | `FINAL_RESULTS/baselines/coco4/baselines.json` |  |
| VII-D COCO-4 what-if calls FIR (high end) | 158 | 158.2 | match | `FINAL_RESULTS/baselines/coco4/baselines.json` |  |
| VII-E regret range over 9 settings Flickr30k-4 (low end) | 1.7 | 1.7095 | match | `FINAL_RESULTS/baselines/flickr4/baselines.json` |  |
| VII-E regret range over 9 settings Flickr30k-4 (high end) | 2.1 | 2.122 | match | `FINAL_RESULTS/baselines/flickr4/baselines.json` |  |
| VII-E max false re-tunes per run Flickr30k-4 | None | 0.15 | info | `FINAL_RESULTS/baselines/flickr4/baselines.json` |  |
| VII-E false re-tunes at >=300 queries, 3 sigma Flickr30k-4 | 0 | 0 | match | `FINAL_RESULTS/baselines/flickr4/baselines.json` |  |
| VII-E regret range over 9 settings COCO-4 (low end) | 6.3 | 6.3293 | match | `FINAL_RESULTS/baselines/coco4/baselines.json` |  |
| VII-E regret range over 9 settings COCO-4 (high end) | 7.6 | 7.5577 | match | `FINAL_RESULTS/baselines/coco4/baselines.json` |  |
| VII-E max false re-tunes per run COCO-4 | None | 0.15 | info | `FINAL_RESULTS/baselines/coco4/baselines.json` |  |
| VII-E false re-tunes at >=300 queries, 3 sigma COCO-4 | 0 | 0 | match | `FINAL_RESULTS/baselines/coco4/baselines.json` |  |
| VII-E regret range over 9 settings COCO-6 (low end) | 7.2 | 7.247 | match | `FINAL_RESULTS/baselines/coco6/baselines.json` |  |
| VII-E regret range over 9 settings COCO-6 (high end) | 8.7 | 8.6563 | match | `FINAL_RESULTS/baselines/coco6/baselines.json` |  |
| VII-E max false re-tunes per run COCO-6 | None | 0.05 | info | `FINAL_RESULTS/baselines/coco6/baselines.json` |  |
| VII-E false re-tunes at >=300 queries, 3 sigma COCO-6 | 0 | 0 | match | `FINAL_RESULTS/baselines/coco6/baselines.json` |  |
| VII-E regret range over 9 settings Synthetic (low end) | 2.8 | 2.8422 | match | `FINAL_RESULTS/baselines/synthetic/baselines.json` |  |
| VII-E regret range over 9 settings Synthetic (high end) | 3.5 | 3.5061 | match | `FINAL_RESULTS/baselines/synthetic/baselines.json` |  |
| VII-E max false re-tunes per run Synthetic | None | 0.05 | info | `FINAL_RESULTS/baselines/synthetic/baselines.json` |  |
| VII-E false re-tunes at >=300 queries, 3 sigma Synthetic | 0 | 0 | match | `FINAL_RESULTS/baselines/synthetic/baselines.json` |  |
| Table V Flickr30k-4 abrupt default | 0.8 | 0.8002 | match | `FINAL_RESULTS/extensions/flickr4/extensions.json` |  |
| Table V Flickr30k-4 abrupt fast path | 0.7 | 0.6527 | match | `FINAL_RESULTS/extensions/flickr4/extensions.json` |  |
| Table V Flickr30k-4 gradual default | 0.5 | 0.5229 | match | `FINAL_RESULTS/extensions/flickr4/extensions.json` |  |
| Table V Flickr30k-4 gradual fast path | 0.2 | 0.213 | match | `FINAL_RESULTS/extensions/flickr4/extensions.json` |  |
| Table V Flickr30k-4 recurring default | 3.3 | 3.2994 | match | `FINAL_RESULTS/extensions/flickr4/extensions.json` |  |
| Table V Flickr30k-4 recurring fast path | 2.0 | 2.0148 | match | `FINAL_RESULTS/extensions/flickr4/extensions.json` |  |
| Table V Flickr30k-4 new_type default | 2.0 | 2.0078 | match | `FINAL_RESULTS/extensions/flickr4/extensions.json` |  |
| Table V Flickr30k-4 new_type fast path | 1.1 | 1.1077 | match | `FINAL_RESULTS/extensions/flickr4/extensions.json` |  |
| VII-F fast path false re-tunes Flickr30k-4 | 0 | 0 | match | `FINAL_RESULTS/extensions/flickr4/extensions.json` |  |
| VII-F fast sweep false re-tunes Flickr30k-4 | 0 | 0 | match | `FINAL_RESULTS/extensions/flickr4/extensions.json` |  |
| Table V COCO-4 abrupt default | 5.8 | 5.7516 | match | `FINAL_RESULTS/extensions/coco4/extensions.json` |  |
| Table V COCO-4 abrupt fast path | 4.3 | 4.3257 | match | `FINAL_RESULTS/extensions/coco4/extensions.json` |  |
| Table V COCO-4 gradual default | 2.7 | 2.7031 | match | `FINAL_RESULTS/extensions/coco4/extensions.json` |  |
| Table V COCO-4 gradual fast path | 1.6 | 1.5853 | match | `FINAL_RESULTS/extensions/coco4/extensions.json` |  |
| Table V COCO-4 recurring default | 7.9 | 7.8712 | match | `FINAL_RESULTS/extensions/coco4/extensions.json` |  |
| Table V COCO-4 recurring fast path | 4.7 | 4.7412 | match | `FINAL_RESULTS/extensions/coco4/extensions.json` |  |
| Table V COCO-4 new_type default | 6.4 | 6.3557 | match | `FINAL_RESULTS/extensions/coco4/extensions.json` |  |
| Table V COCO-4 new_type fast path | 3.8 | 3.8142 | match | `FINAL_RESULTS/extensions/coco4/extensions.json` |  |
| VII-F fast path false re-tunes COCO-4 | 0 | 0 | match | `FINAL_RESULTS/extensions/coco4/extensions.json` |  |
| VII-F fast sweep false re-tunes COCO-4 | 0 | 0 | match | `FINAL_RESULTS/extensions/coco4/extensions.json` |  |
| Table V COCO-6 abrupt default | -1.4 | -1.4484 | match | `FINAL_RESULTS/extensions/coco6/extensions.json` |  |
| Table V COCO-6 abrupt fast path | -3.0 | -2.9671 | match | `FINAL_RESULTS/extensions/coco6/extensions.json` |  |
| Table V COCO-6 gradual default | 2.1 | 2.1029 | match | `FINAL_RESULTS/extensions/coco6/extensions.json` |  |
| Table V COCO-6 gradual fast path | 1.2 | 1.2145 | match | `FINAL_RESULTS/extensions/coco6/extensions.json` |  |
| Table V COCO-6 recurring default | 11.6 | 11.5697 | match | `FINAL_RESULTS/extensions/coco6/extensions.json` |  |
| Table V COCO-6 recurring fast path | 7.3 | 7.2889 | match | `FINAL_RESULTS/extensions/coco6/extensions.json` |  |
| Table V COCO-6 new_type default | 16.3 | 16.2553 | match | `FINAL_RESULTS/extensions/coco6/extensions.json` |  |
| Table V COCO-6 new_type fast path | 9.8 | 9.8498 | match | `FINAL_RESULTS/extensions/coco6/extensions.json` |  |
| VII-F fast path false re-tunes COCO-6 | 0 | 0 | match | `FINAL_RESULTS/extensions/coco6/extensions.json` |  |
| VII-F fast sweep false re-tunes COCO-6 | 0 | 0 | match | `FINAL_RESULTS/extensions/coco6/extensions.json` |  |
| Table V Synthetic-5 abrupt default | 2.2 | 2.1519 | match | `FINAL_RESULTS/extensions/synthetic/extensions_synthetic.json` |  |
| Table V Synthetic-5 abrupt fast path | 1.4 | 1.4029 | match | `FINAL_RESULTS/extensions/synthetic/extensions_synthetic.json` |  |
| Table V Synthetic-5 gradual default | 0.9 | 0.8863 | match | `FINAL_RESULTS/extensions/synthetic/extensions_synthetic.json` |  |
| Table V Synthetic-5 gradual fast path | 0.8 | 0.836 | match | `FINAL_RESULTS/extensions/synthetic/extensions_synthetic.json` |  |
| Table V Synthetic-5 recurring default | 5.9 | 5.8759 | match | `FINAL_RESULTS/extensions/synthetic/extensions_synthetic.json` |  |
| Table V Synthetic-5 recurring fast path | 3.2 | 3.1994 | match | `FINAL_RESULTS/extensions/synthetic/extensions_synthetic.json` |  |
| Table V Synthetic-5 new_type default | 6.2 | 6.1763 | match | `FINAL_RESULTS/extensions/synthetic/extensions_synthetic.json` |  |
| Table V Synthetic-5 new_type fast path | 3.6 | 3.5913 | match | `FINAL_RESULTS/extensions/synthetic/extensions_synthetic.json` |  |
| VII-F fast path false re-tunes Synthetic-5 | 0 | 0 | match | `FINAL_RESULTS/extensions/synthetic/extensions_synthetic.json` |  |
| VII-F fast sweep false re-tunes Synthetic-5 | 0 | 0 | match | `FINAL_RESULTS/extensions/synthetic/extensions_synthetic.json` |  |
| VII-G fast path reduces regret by up to 40% (real data), recomputed from Table V | 40 | 60.0 | MISMATCH | `Table V printed` |  |
| VII-F Flickr Qw=1000 Static vs FIR mean % | -16 | -15.9623 | match | `ext flickr4` |  |
| VII-F Flickr Qw=1000 Static vs FIR recurring % | -37 | -36.7369 | match | `ext flickr4` |  |
| VII-F Flickr Qw=1000 FIR+SR vs FIR mean % | -15.2 | -15.1693 | match | `ext flickr4` |  |
| VII-F COCO-6 recurring Qw=1000 FIR+SR saving % | None | -14.2465 | info | `ext coco6` | printed: saves 14-16% |
| VII-F COCO-6 recurring Qw=1000 FIR+fast+SR saving % | None | -15.7713 | info | `ext coco6` | printed: saves 14-16% |
| VII-F waiting costs at most X% (FIR+SR, Qw=1000, real) | 5.6 | 5.6038 | match | `ext files` |  |
| VII-F high traffic SR vs immediate, max |diff| % | 0.2 | 0.197 | match | `ext files` |  |
| VII-F Static up to X% more at high traffic | 67 | 67.3938 | match | `ext files` |  |
| VII-F FIR+fast+SR never worse than default by more than % (real) | 3.8 | 3.7868 | match | `ext files` |  |
| VII-F same, synthetic (claim says every dataset) | None | 11.4391 | info | `ext synthetic` | exceeds 3.8; claim holds on real data only |
| VII-F FIR+fast+SR within X points of best mean (real) | 1.1 | 1.1207 | match | `ext files` |  |
| VII-F same, synthetic | None | 1.2954 | info | `ext synthetic` | exceeds 1.1; claim holds on real data only |
| Abstract: post-drift cost reduced by 3-34% (from Table III) (low end) | 3 | 2.7 | match | `Table III printed` |  |
| Abstract: post-drift cost reduced by 3-34% (from Table III) (high end) | 34 | 34.4 | match | `Table III printed` |  |
| Intro: static up to 2.5x more expensive (COCO-6 new type, Static/Oracle mean) | 2.5 | 2.5127 | match | `FINAL_RESULTS/baselines/coco6/baselines.json` | a mean over 5 seeds, not a maximum; per-seed max 4.78x |
| VII-C 12 columns what-if saving (x) | 3.1 | 3.1399 | match | `runs/synthetic/fir_mint_v4_results/ablation_candidates.json` |  |
| VII-C 12 columns gap closed (%) | 96 | 95.8751 | match | `runs/synthetic/fir_mint_v4_results/ablation_candidates.json` |  |
| VII-C K=3 saving (x) | 9.4 | 9.3738 | match | `runs/synthetic/fir_mint_v4_results/ablation_candidates.json` |  |
| VII-C K=3 gap (%) | 65 | 64.7157 | match | `runs/synthetic/fir_mint_v4_results/ablation_candidates.json` |  |
| VII-C K=12 saving (x) | 2.1 | 2.0522 | match | `runs/synthetic/fir_mint_v4_results/ablation_candidates.json` |  |
| VII-C K=12 gap (%) | 100 | 100.0 | match | `runs/synthetic/fir_mint_v4_results/ablation_candidates.json` |  |
| Review #10: COCO-6 new type FIR vs Static, paired, in the E4 run | None | -45.0268 | info | `FINAL_RESULTS/baselines/coco6/baselines.json` | Table III prints -30.9 from the E3 run; the two runs are calibrated separately |

## Detail

- E1 COCO-4 (CPU host): FIR vs Static per seed % = [-22.5, 2.2, -23.4, -56.2, 3.6]
- E1 COCO-4 (H100 host): FIR vs Static per seed % = [-8.5, -13.8, -11.0, -11.3, -20.0]
- E1 COCO-6: FIR vs Static per seed % = [-23.9, 0.3, -27.6, -0.2, -14.5]
- E1 Flickr30k-4: FIR vs Static per seed % = [-11.4, -1.3, -12.1, -33.5, -16.4]
- E1 Synthetic-4: FIR vs Static per seed % = [-15.7, -20.1, -28.3, -21.1, -6.2]
- E3 COCO-4 (CPU host): FIR+detector delay per seed/scenario = [11, 11, 11, 11, 11, 12, 12, 13, 13, 13, 9, 9, 9, 9, 9, 11, 11, 11, 11, 11]
- E3 COCO-4 (H100 host): FIR+detector delay per seed/scenario = [11, 11, 11, 11, 11, 12, 12, 13, 13, 13, 9, 9, 9, 9, 9, 11, 11, 11, 11, 11]
- E3 COCO-6: FIR+detector delay per seed/scenario = [11, 11, 11, 11, 11, 14, 12, 13, 13, 12, 9, 9, 9, 9, 9, 11, 11, 11, 11, 11]
- E3 Flickr30k-4: FIR+detector delay per seed/scenario = [11, 11, 11, 11, 11, 12, 12, 14, 13, 13, 9, 9, 9, 9, 9, 11, 11, 11, 11, 11]
- E3 Synthetic-4: FIR+detector delay per seed/scenario = [11, 11, 11, 11, 11, 12, 13, 12, 12, 14, 9, 9, 9, 9, 9, 11, 11, 11, 11, 11]
- Ablation settings ['Adaptive (3..8, 80%)', 'K=1', 'K=12', 'K=2', 'K=3', 'K=5', 'K=8'], C values [6, 8, 12]
-   ablation C=6 Adaptive (3..8, 80%): saving 0.75x, gap closed 95.3%
-   ablation C=6 K=1: saving 6.42x, gap closed 55.7%
-   ablation C=6 K=12: saving 0.47x, gap closed 95.5%
-   ablation C=6 K=2: saving 3.79x, gap closed 75.9%
-   ablation C=6 K=3: saving 2.51x, gap closed 78.4%
-   ablation C=6 K=5: saving 1.37x, gap closed 89.6%
-   ablation C=6 K=8: saving 0.75x, gap closed 95.3%
-   ablation C=8 Adaptive (3..8, 80%): saving 1.77x, gap closed 98.2%
-   ablation C=8 K=1: saving 12.24x, gap closed 51.3%
-   ablation C=8 K=12: saving 1.11x, gap closed 100.0%
-   ablation C=8 K=2: saving 7.54x, gap closed 80.2%
-   ablation C=8 K=3: saving 5.30x, gap closed 83.6%
-   ablation C=8 K=5: saving 3.05x, gap closed 95.1%
-   ablation C=8 K=8: saving 1.77x, gap closed 98.2%
-   ablation C=12 Adaptive (3..8, 80%): saving 3.14x, gap closed 95.9%
-   ablation C=12 K=1: saving 22.54x, gap closed 53.5%
-   ablation C=12 K=12: saving 2.05x, gap closed 100.0%
-   ablation C=12 K=2: saving 13.93x, gap closed 63.4%
-   ablation C=12 K=3: saving 9.37x, gap closed 64.7%
-   ablation C=12 K=5: saving 5.36x, gap closed 85.9%
-   ablation C=12 K=8: saving 3.14x, gap closed 95.9%
- pilot.json keys: ['results', 'timings']
- Method text 'build 4-12 s, re-tune about 1 ms (Flickr30k, 3 seeds)' -> runs/pilot_mint_flickr/pilot.md: build 3.95-12.43 s, what-if wall 0.75-1.62 ms. Matches.