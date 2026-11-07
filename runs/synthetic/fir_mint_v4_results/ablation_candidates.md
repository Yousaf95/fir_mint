# Ablation: FIR candidate count

Cost ratio = workload cost of FIR's configuration / full re-tune (1.00 = same quality). Gap closed = share of the static-vs-full cost gap that FIR recovers. Mean over 5 seeds.

## 6 columns

| FIR setting | What-if calls | Full calls | Speed-up | Cost ratio | Gap closed |
|---|---|---|---|---|---|
| K=1 | 632 | 4052 | 6.4× | 1.158 | 56% |
| K=2 | 1068 | 4052 | 3.8× | 1.078 | 76% |
| K=3 | 1617 | 4052 | 2.5× | 1.068 | 78% |
| K=5 | 2969 | 4052 | 1.4× | 1.034 | 90% |
| K=8 | 5439 | 4052 | 0.8× | 1.009 | 95% |
| K=12 | 8911 | 4052 | 0.5× | 1.008 | 95% |
| Adaptive (3..8, 80%) | 5439 | 4052 | 0.8× | 1.009 | 95% |

## 8 columns

| FIR setting | What-if calls | Full calls | Speed-up | Cost ratio | Gap closed |
|---|---|---|---|---|---|
| K=1 | 1177 | 14408 | 12.2× | 1.155 | 51% |
| K=2 | 1918 | 14408 | 7.5× | 1.073 | 80% |
| K=3 | 2732 | 14408 | 5.3× | 1.062 | 84% |
| K=5 | 4757 | 14408 | 3.0× | 1.017 | 95% |
| K=8 | 8204 | 14408 | 1.8× | 1.008 | 98% |
| K=12 | 13035 | 14408 | 1.1× | 1.000 | 100% |
| Adaptive (3..8, 80%) | 8204 | 14408 | 1.8× | 1.008 | 98% |

## 12 columns

| FIR setting | What-if calls | Full calls | Speed-up | Cost ratio | Gap closed |
|---|---|---|---|---|---|
| K=1 | 2165 | 48580 | 22.5× | 1.155 | 54% |
| K=2 | 3494 | 48580 | 13.9× | 1.123 | 63% |
| K=3 | 5200 | 48580 | 9.4× | 1.118 | 65% |
| K=5 | 9104 | 48580 | 5.4× | 1.046 | 86% |
| K=8 | 15510 | 48580 | 3.1× | 1.015 | 96% |
| K=12 | 23739 | 48580 | 2.1× | 1.000 | 100% |
| Adaptive (3..8, 80%) | 15510 | 48580 | 3.1× | 1.015 | 96% |
