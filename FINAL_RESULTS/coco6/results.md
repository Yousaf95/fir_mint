# FIR-MINT v4 results

Settings: N=30000, dim/column=512, k=10, pool=40, HNSW M=32, efSearch=256, recall target=0.9, extra storage budget=8, FIR candidates=3..8 (cover 80%), window=300 queries, seeds=5. Values are mean ± std over seeds.

## E1. Measured performance after abrupt drift (C=4, FAISS HNSW)

| Policy | Latency (ms) | p95 (ms) | Min recall | Recall-violating mass | What-if calls | Tuning (s) | New indexes | Build (s) |
|---|---|---|---|---|---|---|---|---|
| Static | 4.911 ± 0.686 | 11.532 ± 0.878 | 0.955 ± 0.058 | 0.001 ± 0.002 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| FIR-MINT | 4.211 ± 0.528 | 11.228 ± 0.709 | 0.969 ± 0.033 | 0.000 ± 0.000 | 155.800 ± 5.381 | 0.009 ± 0.001 | 2.200 ± 0.748 | 7.609 ± 1.978 |
| Full re-tune | 4.034 ± 0.578 | 10.342 ± 1.708 | 0.966 ± 0.039 | 0.000 ± 0.000 | 160.000 ± 5.727 | 0.006 ± 0.000 | 2.800 ± 0.748 | 9.989 ± 1.931 |

## E3. Drift scenarios (C=6, 30 windows, estimator-based cost per window)

| Scenario | Policy | Mean cost (ms) | Post-onset cost (ms) | Recall-violating mass | Re-tunes | False re-tunes | What-if calls | Index builds |
|---|---|---|---|---|---|---|---|---|
| abrupt | Static | 4.025 ± 1.433 | 4.232 ± 1.713 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0 | 0.0 |
| abrupt | FIR+detector | 3.380 ± 1.137 | 3.265 ± 1.157 | 0.000 ± 0.000 | 1.000 ± 0.000 | 0.000 ± 0.000 | 147 | 3.0 |
| abrupt | Full+detector | 3.368 ± 1.126 | 3.247 ± 1.141 | 0.000 ± 0.000 | 1.000 ± 0.000 | 0.000 ± 0.000 | 153 | 3.0 |
| abrupt | Full every window | 3.326 ± 1.111 | 3.188 ± 1.102 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 3577 | 31.4 |
| gradual | Static | 4.003 ± 1.523 | 4.211 ± 1.735 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0 | 0.0 |
| gradual | FIR+detector | 3.416 ± 1.165 | 3.331 ± 1.126 | 0.000 ± 0.000 | 2.400 ± 0.490 | 0.000 ± 0.000 | 337 | 4.2 |
| gradual | Full+detector | 3.426 ± 1.177 | 3.346 ± 1.149 | 0.000 ± 0.000 | 2.200 ± 0.400 | 0.000 ± 0.000 | 333 | 3.8 |
| gradual | Full every window | 3.401 ± 1.157 | 3.312 ± 1.117 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 3453 | 34.6 |
| recurring | Static | 3.916 ± 1.475 | 4.029 ± 1.603 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0 | 0.0 |
| recurring | FIR+detector | 3.554 ± 1.278 | 3.535 ± 1.281 | 0.000 ± 0.000 | 3.000 ± 0.000 | 0.000 ± 0.000 | 415 | 7.6 |
| recurring | Full+detector | 3.564 ± 1.271 | 3.549 ± 1.271 | 0.000 ± 0.000 | 3.000 ± 0.000 | 0.000 ± 0.000 | 397 | 8.6 |
| recurring | Full every window | 3.486 ± 1.223 | 3.443 ± 1.195 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 3127 | 33.4 |
| new_type | Static | 4.095 ± 1.721 | 4.331 ± 2.057 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0 | 0.0 |
| new_type | FIR+detector | 3.011 ± 1.078 | 2.706 ± 0.899 | 0.000 ± 0.000 | 1.000 ± 0.000 | 0.000 ± 0.000 | 89 | 1.8 |
| new_type | Full+detector | 3.019 ± 1.079 | 2.718 ± 0.902 | 0.000 ± 0.000 | 1.000 ± 0.000 | 0.000 ± 0.000 | 89 | 1.8 |
| new_type | Full every window | 2.966 ± 1.052 | 2.642 ± 0.864 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 2246 | 36.8 |