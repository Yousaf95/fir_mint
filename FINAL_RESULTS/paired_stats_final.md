# Paired per-seed statistics

Negative = lower latency/cost (better). 95% CI uses the t-distribution over seeds. 'Seeds better' counts seeds where the first policy beats the second.

## /home/$USER/RAO_OCT/results/fir_mint_v4_results_coco_30k_4col/results.json

### E1 (measured, paired by seed)

| Comparison | Metric | Mean change | 95% CI | Seeds better |
|---|---|---|---|---|
| FIR-MINT vs Static | latency | -19.2% | [-49.5%, +11.0%] | 3/5 |
| FIR-MINT vs Static | p95 | -1.0% | [-20.7%, +18.6%] | 2/5 |
| Full re-tune vs Static | latency | -17.6% | [-44.4%, +9.1%] | 3/5 |
| Full re-tune vs Static | p95 | +2.6% | [-9.8%, +15.0%] | 2/5 |
| FIR-MINT vs Full re-tune | latency | -3.0% | [-11.2%, +5.1%] | 3/5 |
| FIR-MINT vs Full re-tune | p95 | -3.8% | [-15.3%, +7.7%] | 3/5 |

Per seed (mean latency, ms):

| Seed | Static | FIR-MINT | Full re-tune | FIR vs Static |
|---|---|---|---|---|
| 0 | 3.203 | 2.482 | 2.478 | -22.5% |
| 1 | 2.104 | 2.151 | 2.132 | +2.2% |
| 2 | 2.404 | 1.842 | 1.860 | -23.4% |
| 3 | 3.687 | 1.616 | 1.894 | -56.2% |
| 4 | 1.837 | 1.904 | 1.917 | +3.6% |

### E3 (estimated post-onset cost, paired by seed)

| Scenario | Comparison | Mean change | 95% CI | Seeds better |
|---|---|---|---|---|
| abrupt | FIR+detector vs Static | -13.3% | [-24.5%, -2.1%] | 5/5 |
| abrupt | Full+detector vs Static | -13.5% | [-24.8%, -2.2%] | 5/5 |
| abrupt | FIR+detector vs Full+detector | +0.2% | [-0.4%, +0.9%] | 0/5 |
| abrupt | FIR+detector vs Full every window | +0.3% | [-1.6%, +2.1%] | 3/5 |
| gradual | FIR+detector vs Static | -18.0% | [-23.7%, -12.3%] | 5/5 |
| gradual | Full+detector vs Static | -18.0% | [-23.6%, -12.4%] | 5/5 |
| gradual | FIR+detector vs Full+detector | +0.1% | [-0.7%, +0.8%] | 2/5 |
| gradual | FIR+detector vs Full every window | -0.1% | [-1.3%, +1.0%] | 4/5 |
| recurring | FIR+detector vs Static | -9.4% | [-18.6%, -0.2%] | 5/5 |
| recurring | Full+detector vs Static | -7.4% | [-14.9%, +0.1%] | 5/5 |
| recurring | FIR+detector vs Full+detector | -2.3% | [-5.5%, +1.0%] | 5/5 |
| recurring | FIR+detector vs Full every window | -0.4% | [-2.8%, +2.1%] | 3/5 |
| new_type | FIR+detector vs Static | -28.1% | [-49.4%, -6.8%] | 4/5 |
| new_type | Full+detector vs Static | -28.3% | [-49.8%, -6.8%] | 4/5 |
| new_type | FIR+detector vs Full+detector | +0.3% | [-0.6%, +1.2%] | 1/5 |
| new_type | FIR+detector vs Full every window | +2.4% | [-0.1%, +5.0%] | 1/5 |

## /home/$USER/RAO_OCT/fir_mint_v4_results_coco_30k_4col_gpu/results.json

### E1 (measured, paired by seed)

| Comparison | Metric | Mean change | 95% CI | Seeds better |
|---|---|---|---|---|
| FIR-MINT vs Static | latency | -12.9% | [-18.3%, -7.5%] | 5/5 |
| FIR-MINT vs Static | p95 | +8.8% | [-22.6%, +40.1%] | 3/5 |
| Full re-tune vs Static | latency | -15.3% | [-20.2%, -10.3%] | 5/5 |
| Full re-tune vs Static | p95 | +2.6% | [-35.7%, +40.9%] | 4/5 |
| FIR-MINT vs Full re-tune | latency | +2.9% | [-4.1%, +9.8%] | 1/5 |
| FIR-MINT vs Full re-tune | p95 | +8.7% | [-14.8%, +32.2%] | 2/5 |

Per seed (mean latency, ms):

| Seed | Static | FIR-MINT | Full re-tune | FIR vs Static |
|---|---|---|---|---|
| 0 | 3.546 | 3.243 | 2.875 | -8.5% |
| 1 | 2.440 | 2.103 | 2.105 | -13.8% |
| 2 | 2.977 | 2.649 | 2.629 | -11.0% |
| 3 | 2.277 | 2.020 | 2.008 | -11.3% |
| 4 | 3.090 | 2.473 | 2.468 | -20.0% |

### E3 (estimated post-onset cost, paired by seed)

| Scenario | Comparison | Mean change | 95% CI | Seeds better |
|---|---|---|---|---|
| abrupt | FIR+detector vs Static | -5.9% | [-13.2%, +1.5%] | 4/5 |
| abrupt | Full+detector vs Static | -4.2% | [-7.0%, -1.4%] | 5/5 |
| abrupt | FIR+detector vs Full+detector | -1.8% | [-7.3%, +3.7%] | 2/5 |
| abrupt | FIR+detector vs Full every window | -1.9% | [-5.2%, +1.3%] | 4/5 |
| gradual | FIR+detector vs Static | -13.4% | [-28.7%, +1.9%] | 4/5 |
| gradual | Full+detector vs Static | -12.7% | [-27.6%, +2.2%] | 4/5 |
| gradual | FIR+detector vs Full+detector | -0.9% | [-3.5%, +1.8%] | 2/5 |
| gradual | FIR+detector vs Full every window | -0.2% | [-1.6%, +1.2%] | 4/5 |
| recurring | FIR+detector vs Static | -6.1% | [-15.0%, +2.7%] | 4/5 |
| recurring | Full+detector vs Static | -5.1% | [-12.3%, +2.0%] | 3/5 |
| recurring | FIR+detector vs Full+detector | -1.1% | [-3.8%, +1.5%] | 3/5 |
| recurring | FIR+detector vs Full every window | -0.0% | [-1.9%, +1.9%] | 3/5 |
| new_type | FIR+detector vs Static | -34.4% | [-66.8%, -1.9%] | 5/5 |
| new_type | Full+detector vs Static | -34.4% | [-66.8%, -1.9%] | 5/5 |
| new_type | FIR+detector vs Full+detector | +0.1% | [-0.6%, +0.8%] | 2/5 |
| new_type | FIR+detector vs Full every window | +5.7% | [-2.9%, +14.3%] | 0/5 |

## /home/$USER/RAO_OCT/runs/fir_mint_v4_results_coco_30k_6col/results.json

### E1 (measured, paired by seed)

| Comparison | Metric | Mean change | 95% CI | Seeds better |
|---|---|---|---|---|
| FIR-MINT vs Static | latency | -13.2% | [-29.3%, +3.0%] | 4/5 |
| FIR-MINT vs Static | p95 | -2.4% | [-9.6%, +4.8%] | 3/5 |
| Full re-tune vs Static | latency | -16.7% | [-34.8%, +1.3%] | 5/5 |
| Full re-tune vs Static | p95 | -9.2% | [-35.4%, +17.0%] | 3/5 |
| FIR-MINT vs Full re-tune | latency | +5.1% | [-7.0%, +17.1%] | 1/5 |
| FIR-MINT vs Full re-tune | p95 | +11.7% | [-16.1%, +39.5%] | 1/5 |

Per seed (mean latency, ms):

| Seed | Static | FIR-MINT | Full re-tune | FIR vs Static |
|---|---|---|---|---|
| 0 | 5.749 | 4.373 | 4.631 | -23.9% |
| 1 | 5.137 | 5.152 | 4.690 | +0.3% |
| 2 | 5.221 | 3.778 | 3.166 | -27.6% |
| 3 | 3.696 | 3.689 | 3.675 | -0.2% |
| 4 | 4.750 | 4.063 | 4.009 | -14.5% |

### E3 (estimated post-onset cost, paired by seed)

| Scenario | Comparison | Mean change | 95% CI | Seeds better |
|---|---|---|---|---|
| abrupt | FIR+detector vs Static | -21.6% | [-30.8%, -12.5%] | 5/5 |
| abrupt | Full+detector vs Static | -22.0% | [-31.1%, -12.8%] | 5/5 |
| abrupt | FIR+detector vs Full+detector | +0.4% | [-0.6%, +1.5%] | 0/5 |
| abrupt | FIR+detector vs Full every window | +2.2% | [+0.1%, +4.3%] | 1/5 |
| gradual | FIR+detector vs Static | -17.8% | [-29.6%, -6.0%] | 5/5 |
| gradual | Full+detector vs Static | -17.7% | [-28.8%, -6.6%] | 5/5 |
| gradual | FIR+detector vs Full+detector | -0.2% | [-1.4%, +1.0%] | 3/5 |
| gradual | FIR+detector vs Full every window | +0.5% | [+0.1%, +0.9%] | 1/5 |
| recurring | FIR+detector vs Static | -11.1% | [-20.1%, -2.1%] | 5/5 |
| recurring | Full+detector vs Static | -10.5% | [-19.8%, -1.2%] | 5/5 |
| recurring | FIR+detector vs Full+detector | -0.7% | [-1.8%, +0.5%] | 4/5 |
| recurring | FIR+detector vs Full every window | +1.8% | [-2.3%, +5.9%] | 2/5 |
| new_type | FIR+detector vs Static | -30.9% | [-56.7%, -5.1%] | 5/5 |
| new_type | Full+detector vs Static | -30.7% | [-56.3%, -5.1%] | 5/5 |
| new_type | FIR+detector vs Full+detector | -0.4% | [-1.3%, +0.5%] | 3/5 |
| new_type | FIR+detector vs Full every window | +2.0% | [-2.1%, +6.0%] | 2/5 |

## /home/$USER/RAO_OCT/runs/fir_mint_v4_results_flickr_28k_4col/results.json

### E1 (measured, paired by seed)

| Comparison | Metric | Mean change | 95% CI | Seeds better |
|---|---|---|---|---|
| FIR-MINT vs Static | latency | -14.9% | [-29.6%, -0.3%] | 5/5 |
| FIR-MINT vs Static | p95 | -21.6% | [-49.9%, +6.7%] | 5/5 |
| Full re-tune vs Static | latency | -15.6% | [-30.2%, -0.9%] | 5/5 |
| Full re-tune vs Static | p95 | -21.4% | [-49.4%, +6.7%] | 5/5 |
| FIR-MINT vs Full re-tune | latency | +0.8% | [-1.1%, +2.7%] | 2/5 |
| FIR-MINT vs Full re-tune | p95 | -0.4% | [-1.8%, +1.0%] | 2/5 |

Per seed (mean latency, ms):

| Seed | Static | FIR-MINT | Full re-tune | FIR vs Static |
|---|---|---|---|---|
| 0 | 1.921 | 1.702 | 1.645 | -11.4% |
| 1 | 1.415 | 1.397 | 1.398 | -1.3% |
| 2 | 1.629 | 1.431 | 1.431 | -12.1% |
| 3 | 2.278 | 1.514 | 1.505 | -33.5% |
| 4 | 1.702 | 1.423 | 1.424 | -16.4% |

### E3 (estimated post-onset cost, paired by seed)

| Scenario | Comparison | Mean change | 95% CI | Seeds better |
|---|---|---|---|---|
| abrupt | FIR+detector vs Static | -7.4% | [-10.6%, -4.1%] | 5/5 |
| abrupt | Full+detector vs Static | -8.2% | [-12.5%, -3.9%] | 5/5 |
| abrupt | FIR+detector vs Full+detector | +1.0% | [-0.8%, +2.7%] | 0/5 |
| abrupt | FIR+detector vs Full every window | +1.1% | [-1.7%, +3.9%] | 3/5 |
| gradual | FIR+detector vs Static | -4.8% | [-9.3%, -0.3%] | 4/5 |
| gradual | Full+detector vs Static | -4.6% | [-9.0%, -0.3%] | 4/5 |
| gradual | FIR+detector vs Full+detector | -0.2% | [-0.4%, +0.1%] | 3/5 |
| gradual | FIR+detector vs Full every window | +0.1% | [-0.3%, +0.5%] | 2/5 |
| recurring | FIR+detector vs Static | -2.7% | [-5.5%, +0.2%] | 4/5 |
| recurring | Full+detector vs Static | -2.6% | [-5.1%, +0.0%] | 4/5 |
| recurring | FIR+detector vs Full+detector | -0.1% | [-0.6%, +0.4%] | 2/5 |
| recurring | FIR+detector vs Full every window | +0.7% | [-0.2%, +1.6%] | 1/5 |
| new_type | FIR+detector vs Static | -11.9% | [-20.8%, -3.0%] | 5/5 |
| new_type | Full+detector vs Static | -11.9% | [-20.8%, -3.1%] | 5/5 |
| new_type | FIR+detector vs Full+detector | +0.0% | [-0.0%, +0.1%] | 0/5 |
| new_type | FIR+detector vs Full every window | +0.5% | [-0.4%, +1.4%] | 2/5 |

## /home/$USER/RAO_OCT/runs/synthetic/fir_mint_v4_results/results.json

### E1 (measured, paired by seed)

| Comparison | Metric | Mean change | 95% CI | Seeds better |
|---|---|---|---|---|
| FIR-MINT vs Static | latency | -18.3% | [-28.4%, -8.2%] | 5/5 |
| FIR-MINT vs Static | p95 | -3.7% | [-24.7%, +17.2%] | 4/5 |
| Full re-tune vs Static | latency | -18.4% | [-29.0%, -7.8%] | 5/5 |
| Full re-tune vs Static | p95 | -7.5% | [-22.5%, +7.5%] | 4/5 |
| FIR-MINT vs Full re-tune | latency | +0.3% | [-4.3%, +4.9%] | 3/5 |
| FIR-MINT vs Full re-tune | p95 | +4.0% | [-9.2%, +17.2%] | 2/5 |

Per seed (mean latency, ms):

| Seed | Static | FIR-MINT | Full re-tune | FIR vs Static |
|---|---|---|---|---|
| 0 | 0.580 | 0.489 | 0.465 | -15.7% |
| 1 | 0.663 | 0.530 | 0.556 | -20.1% |
| 2 | 0.655 | 0.470 | 0.471 | -28.3% |
| 3 | 0.642 | 0.507 | 0.496 | -21.1% |
| 4 | 0.627 | 0.588 | 0.594 | -6.2% |

### E3 (estimated post-onset cost, paired by seed)

| Scenario | Comparison | Mean change | 95% CI | Seeds better |
|---|---|---|---|---|
| abrupt | FIR+detector vs Static | -23.1% | [-32.3%, -13.9%] | 5/5 |
| abrupt | Full+detector vs Static | -21.9% | [-31.0%, -12.9%] | 5/5 |
| abrupt | FIR+detector vs Full+detector | -1.5% | [-6.0%, +3.1%] | 1/5 |
| abrupt | FIR+detector vs Full every window | +1.1% | [-1.2%, +3.4%] | 1/5 |
| gradual | FIR+detector vs Static | -16.5% | [-25.2%, -7.7%] | 5/5 |
| gradual | Full+detector vs Static | -16.7% | [-25.2%, -8.2%] | 5/5 |
| gradual | FIR+detector vs Full+detector | +0.3% | [-0.6%, +1.2%] | 3/5 |
| gradual | FIR+detector vs Full every window | +0.8% | [-0.7%, +2.3%] | 2/5 |
| recurring | FIR+detector vs Static | -15.9% | [-19.3%, -12.6%] | 5/5 |
| recurring | Full+detector vs Static | -16.6% | [-20.4%, -12.8%] | 5/5 |
| recurring | FIR+detector vs Full+detector | +0.8% | [-0.0%, +1.6%] | 1/5 |
| recurring | FIR+detector vs Full every window | +4.7% | [+2.7%, +6.7%] | 0/5 |
| new_type | FIR+detector vs Static | -32.3% | [-41.0%, -23.7%] | 5/5 |
| new_type | Full+detector vs Static | -32.4% | [-41.0%, -23.8%] | 5/5 |
| new_type | FIR+detector vs Full+detector | +0.0% | [-0.2%, +0.3%] | 1/5 |
| new_type | FIR+detector vs Full every window | +2.5% | [+1.1%, +3.9%] | 0/5 |
