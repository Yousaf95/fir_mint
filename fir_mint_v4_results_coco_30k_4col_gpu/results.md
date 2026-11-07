# FIR-MINT v4 results

Settings: N=30000, dim/column=512, k=10, pool=40, HNSW M=32, efSearch=256, recall target=0.9, extra storage budget=8, FIR candidates=3..8 (cover 80%), window=300 queries, seeds=5. Values are mean ± std over seeds.

## E1. Measured performance after abrupt drift (C=4, FAISS HNSW)

| Policy | Latency (ms) | p95 (ms) | Min recall | Recall-violating mass | What-if calls | Tuning (s) | New indexes | Build (s) |
|---|---|---|---|---|---|---|---|---|
| Static | 2.866 ± 0.459 | 6.927 ± 1.591 | 0.992 ± 0.006 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| FIR-MINT | 2.498 ± 0.439 | 7.493 ± 2.010 | 0.995 ± 0.006 | 0.000 ± 0.000 | 53.800 ± 2.638 | 0.001 ± 0.000 | 1.600 ± 0.490 | 22.200 ± 7.194 |
| Full re-tune | 2.417 ± 0.323 | 6.879 ± 1.544 | 0.995 ± 0.006 | 0.000 ± 0.000 | 47.200 ± 2.315 | 0.000 ± 0.000 | 1.600 ± 0.490 | 22.136 ± 7.133 |

## E3. Drift scenarios (C=4, 30 windows, estimator-based cost per window)

| Scenario | Policy | Mean cost (ms) | Post-onset cost (ms) | Recall-violating mass | Re-tunes | False re-tunes | What-if calls | Index builds |
|---|---|---|---|---|---|---|---|---|
| abrupt | Static | 3.003 ± 0.982 | 2.873 ± 0.937 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0 | 0.0 |
| abrupt | FIR+detector | 2.875 ± 0.889 | 2.681 ± 0.788 | 0.000 ± 0.000 | 1.000 ± 0.000 | 0.000 ± 0.000 | 52 | 1.4 |
| abrupt | Full+detector | 2.920 ± 0.949 | 2.749 ± 0.884 | 0.000 ± 0.000 | 1.000 ± 0.000 | 0.000 ± 0.000 | 48 | 1.8 |
| abrupt | Full every window | 2.919 ± 0.911 | 2.745 ± 0.854 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 1377 | 24.8 |
| gradual | Static | 3.430 ± 0.901 | 3.565 ± 0.931 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0 | 0.0 |
| gradual | FIR+detector | 3.152 ± 1.098 | 3.147 ± 1.165 | 0.000 ± 0.000 | 2.800 ± 0.400 | 0.000 ± 0.000 | 131 | 2.8 |
| gradual | Full+detector | 3.170 ± 1.098 | 3.174 ± 1.178 | 0.000 ± 0.000 | 2.800 ± 0.400 | 0.000 ± 0.000 | 131 | 4.4 |
| gradual | Full every window | 3.169 ± 1.125 | 3.163 ± 1.204 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 1341 | 29.8 |
| recurring | Static | 3.329 ± 0.912 | 3.346 ± 0.854 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0 | 0.0 |
| recurring | FIR+detector | 3.205 ± 1.026 | 3.177 ± 0.987 | 0.000 ± 0.000 | 3.000 ± 0.000 | 0.000 ± 0.000 | 153 | 5.8 |
| recurring | Full+detector | 3.225 ± 1.003 | 3.204 ± 0.961 | 0.000 ± 0.000 | 3.000 ± 0.000 | 0.000 ± 0.000 | 139 | 6.4 |
| recurring | Full every window | 3.207 ± 1.027 | 3.179 ± 0.992 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 1333 | 26.0 |
| new_type | Static | 3.950 ± 1.677 | 4.296 ± 2.130 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0 | 0.0 |
| new_type | FIR+detector | 2.772 ± 1.041 | 2.529 ± 0.886 | 0.000 ± 0.000 | 1.000 ± 0.000 | 0.000 ± 0.000 | 48 | 2.0 |
| new_type | Full+detector | 2.774 ± 1.047 | 2.532 ± 0.896 | 0.000 ± 0.000 | 1.000 ± 0.000 | 0.000 ± 0.000 | 47 | 1.6 |
| new_type | Full every window | 2.691 ± 1.007 | 2.406 ± 0.822 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 1219 | 27.0 |