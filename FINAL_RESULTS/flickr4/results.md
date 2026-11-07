# FIR-MINT v4 results

Settings: N=28000, dim/column=512, k=10, pool=40, HNSW M=32, efSearch=256, recall target=0.9, extra storage budget=8, FIR candidates=3..8 (cover 80%), window=300 queries, seeds=5. Values are mean ± std over seeds.

## E1. Measured performance after abrupt drift (C=4, FAISS HNSW)

| Policy | Latency (ms) | p95 (ms) | Min recall | Recall-violating mass | What-if calls | Tuning (s) | New indexes | Build (s) |
|---|---|---|---|---|---|---|---|---|
| Static | 1.789 ± 0.293 | 3.745 ± 1.038 | 0.993 ± 0.003 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| FIR-MINT | 1.494 ± 0.111 | 2.724 ± 0.085 | 0.993 ± 0.003 | 0.000 ± 0.000 | 53.400 ± 2.939 | 0.002 ± 0.000 | 2.000 ± 0.894 | 7.704 ± 3.274 |
| Full re-tune | 1.481 ± 0.090 | 2.735 ± 0.106 | 0.994 ± 0.004 | 0.000 ± 0.000 | 47.600 ± 1.625 | 0.001 ± 0.000 | 2.200 ± 0.748 | 8.050 ± 3.035 |

## E3. Drift scenarios (C=4, 30 windows, estimator-based cost per window)

| Scenario | Policy | Mean cost (ms) | Post-onset cost (ms) | Recall-violating mass | Re-tunes | False re-tunes | What-if calls | Index builds |
|---|---|---|---|---|---|---|---|---|
| abrupt | Static | 1.483 ± 0.048 | 1.724 ± 0.079 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0 | 0.0 |
| abrupt | FIR+detector | 1.398 ± 0.043 | 1.596 ± 0.060 | 0.000 ± 0.000 | 1.000 ± 0.000 | 0.000 ± 0.000 | 50 | 2.0 |
| abrupt | Full+detector | 1.388 ± 0.045 | 1.581 ± 0.066 | 0.000 ± 0.000 | 1.000 ± 0.000 | 0.000 ± 0.000 | 43 | 2.4 |
| abrupt | Full every window | 1.384 ± 0.046 | 1.579 ± 0.069 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 1289 | 19.8 |
| gradual | Static | 1.317 ± 0.039 | 1.474 ± 0.053 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0 | 0.0 |
| gradual | FIR+detector | 1.270 ± 0.054 | 1.404 ± 0.072 | 0.000 ± 0.000 | 2.600 ± 0.490 | 0.000 ± 0.000 | 120 | 2.0 |
| gradual | Full+detector | 1.272 ± 0.054 | 1.406 ± 0.071 | 0.000 ± 0.000 | 2.400 ± 0.490 | 0.000 ± 0.000 | 107 | 2.4 |
| gradual | Full every window | 1.268 ± 0.058 | 1.402 ± 0.075 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 1297 | 23.4 |
| recurring | Static | 1.295 ± 0.058 | 1.409 ± 0.070 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0 | 0.0 |
| recurring | FIR+detector | 1.267 ± 0.058 | 1.371 ± 0.066 | 0.000 ± 0.000 | 3.000 ± 0.000 | 0.000 ± 0.000 | 141 | 5.4 |
| recurring | Full+detector | 1.268 ± 0.058 | 1.372 ± 0.065 | 0.000 ± 0.000 | 3.000 ± 0.000 | 0.000 ± 0.000 | 133 | 7.4 |
| recurring | Full every window | 1.260 ± 0.056 | 1.361 ± 0.063 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 1274 | 19.4 |
| new_type | Static | 1.299 ± 0.070 | 1.449 ± 0.099 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0 | 0.0 |
| new_type | FIR+detector | 1.184 ± 0.096 | 1.277 ± 0.127 | 0.000 ± 0.000 | 1.000 ± 0.000 | 0.000 ± 0.000 | 42 | 1.0 |
| new_type | Full+detector | 1.183 ± 0.096 | 1.276 ± 0.127 | 0.000 ± 0.000 | 1.000 ± 0.000 | 0.000 ± 0.000 | 43 | 1.0 |
| new_type | Full every window | 1.180 ± 0.101 | 1.271 ± 0.134 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 1160 | 25.6 |