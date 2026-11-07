# FIR-MINT v4 results

Settings: N=30000, dim/column=512, k=10, pool=40, HNSW M=32, efSearch=256, recall target=0.9, extra storage budget=8, FIR candidates=3..8 (cover 80%), window=300 queries, seeds=5. Values are mean ± std over seeds.

## E1. Measured performance after abrupt drift (C=4, FAISS HNSW)

| Policy | Latency (ms) | p95 (ms) | Min recall | Recall-violating mass | What-if calls | Tuning (s) | New indexes | Build (s) |
|---|---|---|---|---|---|---|---|---|
| Static | 2.647 ± 0.693 | 6.865 ± 1.197 | 0.992 ± 0.004 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| FIR-MINT | 1.999 ± 0.295 | 6.712 ± 1.056 | 0.995 ± 0.004 | 0.000 ± 0.000 | 54.800 ± 3.763 | 0.001 ± 0.000 | 1.800 ± 0.748 | 25.341 ± 6.348 |
| Full re-tune | 2.056 ± 0.231 | 6.959 ± 0.767 | 0.995 ± 0.004 | 0.000 ± 0.000 | 45.800 ± 2.227 | 0.001 ± 0.000 | 2.000 ± 1.095 | 27.697 ± 10.004 |

## E3. Drift scenarios (C=4, 30 windows, estimator-based cost per window)

| Scenario | Policy | Mean cost (ms) | Post-onset cost (ms) | Recall-violating mass | Re-tunes | False re-tunes | What-if calls | Index builds |
|---|---|---|---|---|---|---|---|---|
| abrupt | Static | 1.098 ± 0.107 | 1.255 ± 0.131 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0 | 0.0 |
| abrupt | FIR+detector | 0.985 ± 0.105 | 1.085 ± 0.123 | 0.000 ± 0.000 | 1.000 ± 0.000 | 0.000 ± 0.000 | 50 | 1.8 |
| abrupt | Full+detector | 0.983 ± 0.103 | 1.082 ± 0.120 | 0.000 ± 0.000 | 1.000 ± 0.000 | 0.000 ± 0.000 | 46 | 2.0 |
| abrupt | Full every window | 0.984 ± 0.101 | 1.081 ± 0.116 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 1342 | 20.0 |
| gradual | Static | 1.095 ± 0.089 | 1.254 ± 0.098 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0 | 0.0 |
| gradual | FIR+detector | 0.944 ± 0.071 | 1.026 ± 0.068 | 0.000 ± 0.000 | 2.800 ± 0.400 | 0.000 ± 0.000 | 136 | 3.2 |
| gradual | Full+detector | 0.943 ± 0.068 | 1.025 ± 0.063 | 0.000 ± 0.000 | 2.800 ± 0.400 | 0.000 ± 0.000 | 129 | 3.2 |
| gradual | Full every window | 0.944 ± 0.065 | 1.027 ± 0.062 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 1328 | 23.2 |
| recurring | Static | 1.043 ± 0.085 | 1.134 ± 0.086 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0 | 0.0 |
| recurring | FIR+detector | 0.963 ± 0.084 | 1.025 ± 0.088 | 0.000 ± 0.000 | 3.000 ± 0.000 | 0.000 ± 0.000 | 152 | 4.8 |
| recurring | Full+detector | 0.980 ± 0.078 | 1.048 ± 0.078 | 0.000 ± 0.000 | 3.000 ± 0.000 | 0.000 ± 0.000 | 137 | 7.4 |
| recurring | Full every window | 0.965 ± 0.082 | 1.029 ± 0.087 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 1314 | 30.8 |
| new_type | Static | 1.114 ± 0.099 | 1.285 ± 0.146 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0 | 0.0 |
| new_type | FIR+detector | 0.864 ± 0.120 | 0.910 ± 0.149 | 0.000 ± 0.000 | 1.000 ± 0.000 | 0.000 ± 0.000 | 46 | 1.0 |
| new_type | Full+detector | 0.862 ± 0.120 | 0.907 ± 0.150 | 0.000 ± 0.000 | 1.000 ± 0.000 | 0.000 ± 0.000 | 46 | 1.2 |
| new_type | Full every window | 0.853 ± 0.127 | 0.890 ± 0.161 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 1210 | 30.2 |