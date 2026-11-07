# FIR-MINT v4 results

Settings: N=30000, dim/column=512, k=10, pool=40, HNSW M=32, efSearch=256, recall target=0.9, extra storage budget=8, FIR candidates=3..8 (cover 80%), window=300 queries, seeds=5. Values are mean ± std over seeds.

## E1. Measured performance after abrupt drift (C=4, FAISS HNSW)

| Policy | Latency (ms) | p95 (ms) | Min recall | Recall-violating mass | What-if calls | Tuning (s) | New indexes | Build (s) |
|---|---|---|---|---|---|---|---|---|
| Static | 6.030 ± 0.682 | 11.607 ± 0.356 | 0.889 ± 0.098 | 0.001 ± 0.001 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| FIR-MINT | 4.383 ± 0.418 | 11.494 ± 0.368 | 0.805 ± 0.181 | 0.001 ± 0.001 | 298.200 ± 7.521 | 0.018 ± 0.005 | 3.000 ± 0.632 | 10.717 ± 2.456 |
| Full re-tune | 4.155 ± 0.409 | 10.763 ± 1.248 | 0.792 ± 0.170 | 0.001 ± 0.001 | 313.200 ± 16.042 | 0.022 ± 0.004 | 3.000 ± 0.632 | 11.394 ± 2.732 |

## E3. Drift scenarios (C=8, 30 windows, estimator-based cost per window)

| Scenario | Policy | Mean cost (ms) | Post-onset cost (ms) | Recall-violating mass | Re-tunes | False re-tunes | What-if calls | Index builds |
|---|---|---|---|---|---|---|---|---|
| abrupt | Static | 5.184 ± 2.207 | 5.673 ± 2.651 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0 | 0.0 |
| abrupt | FIR+detector | 4.355 ± 1.801 | 4.429 ± 2.029 | 0.000 ± 0.000 | 1.000 ± 0.000 | 0.000 ± 0.000 | 291 | 2.6 |
| abrupt | Full+detector | 4.343 ± 1.796 | 4.411 ± 2.020 | 0.000 ± 0.000 | 1.000 ± 0.000 | 0.000 ± 0.000 | 308 | 2.6 |
| abrupt | Full every window | 4.326 ± 1.816 | 4.382 ± 2.055 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 5719 | 46.6 |
| gradual | Static | 4.949 ± 2.098 | 5.344 ± 2.497 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0 | 0.0 |
| gradual | FIR+detector | 4.260 ± 1.584 | 4.311 ± 1.685 | 0.000 ± 0.000 | 2.000 ± 0.000 | 0.000 ± 0.000 | 518 | 4.4 |
| gradual | Full+detector | 4.274 ± 1.619 | 4.331 ± 1.743 | 0.000 ± 0.000 | 2.000 ± 0.000 | 0.000 ± 0.000 | 535 | 4.8 |
| gradual | Full every window | 4.269 ± 1.609 | 4.311 ± 1.709 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 5294 | 50.4 |
| recurring | Static | 4.797 ± 2.105 | 5.025 ± 2.389 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0 | 0.0 |
| recurring | FIR+detector | 4.377 ± 1.726 | 4.452 ± 1.846 | 0.000 ± 0.000 | 3.000 ± 0.000 | 0.000 ± 0.000 | 739 | 7.6 |
| recurring | Full+detector | 4.332 ± 1.673 | 4.391 ± 1.770 | 0.000 ± 0.000 | 3.000 ± 0.000 | 0.000 ± 0.000 | 730 | 8.6 |
| recurring | Full every window | 4.269 ± 1.632 | 4.302 ± 1.710 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 4874 | 54.4 |
| new_type | Static | 4.440 ± 2.102 | 4.554 ± 2.581 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0 | 0.0 |
| new_type | FIR+detector | 3.508 ± 1.145 | 3.156 ± 0.947 | 0.000 ± 0.000 | 1.000 ± 0.000 | 0.000 ± 0.000 | 100 | 1.2 |
| new_type | Full+detector | 3.498 ± 1.143 | 3.141 ± 0.943 | 0.000 ± 0.000 | 1.000 ± 0.000 | 0.000 ± 0.000 | 118 | 2.2 |
| new_type | Full every window | 3.484 ± 1.132 | 3.130 ± 0.930 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 2817 | 47.2 |