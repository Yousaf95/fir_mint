# MINT pilot

This pilot uses a MINT-style reimplementation, not the original MINT code.
It shares the frozen FIR-MINT estimator, FAISS settings, recall target, and data.
Dataset: `flickr_28k_4col`; seeds: [0, 1, 2].
Recall gate (minimum empirical recall >= 0.90): **FAIL**.

| Seed | Policy | Latency ms | p95 ms | Min recall | Gate | What-if calls | Tuning s | Build s | New indexes |
|---:|---|---:|---:|---:|---|---:|---:|---:|---:|
| 0 | Static | 1.769 | 1.769 | 0.800 | FAIL | 0 | 0.0000 | 0.0000 | 0 |
| 0 | FIR-MINT | 1.483 | 1.484 | 0.700 | FAIL | 44 | 0.0011 | 12.4306 | 3 |
| 0 | Full re-tune | 1.461 | 1.470 | 0.700 | FAIL | 50 | 0.0008 | 12.4190 | 3 |
| 0 | MINT-style reimplementation | 1.470 | 1.473 | 0.700 | FAIL | 50 | 0.0014 | 12.4070 | 3 |
| 1 | Static | 1.837 | 1.839 | 0.700 | FAIL | 0 | 0.0000 | 0.0000 | 0 |
| 1 | FIR-MINT | 1.579 | 1.584 | 0.800 | FAIL | 54 | 0.0016 | 11.0696 | 2 |
| 1 | Full re-tune | 1.590 | 1.590 | 0.800 | FAIL | 47 | 0.0007 | 10.9429 | 2 |
| 1 | MINT-style reimplementation | 1.686 | 1.688 | 0.800 | FAIL | 49 | 0.0013 | 3.9471 | 1 |
| 2 | Static | 2.202 | 2.203 | 0.900 | PASS | 0 | 0.0000 | 0.0000 | 0 |
| 2 | FIR-MINT | 1.678 | 1.682 | 0.900 | PASS | 57 | 0.0016 | 8.4133 | 2 |
| 2 | Full re-tune | 1.677 | 1.679 | 0.900 | PASS | 50 | 0.0008 | 8.3747 | 2 |
| 2 | MINT-style reimplementation | 1.677 | 1.680 | 0.900 | PASS | 50 | 0.0014 | 8.4155 | 2 |

## Timing decomposition

Recall-estimation/tuning wall time is reported separately from query latency.

```json
{
  "0": {
    "build_wall_s": {
      "FIR-MINT": 12.43062435882166,
      "Full re-tune": 12.41900153271854,
      "MINT-style reimplementation": 12.407009408809245,
      "Static": 5.308538675308228e-07
    },
    "detect_wall_s": 5.112960934638977e-06,
    "detector_events": 0,
    "swap_wall_s": 3.7567224353551865e-07,
    "whatif_wall_s": {
      "FIR-MINT": 0.0010692761279642582,
      "Full re-tune": 0.000836632214486599,
      "MINT-style reimplementation": 0.0013513159938156605
    }
  },
  "1": {
    "build_wall_s": {
      "FIR-MINT": 11.06959941610694,
      "Full re-tune": 10.94293802138418,
      "MINT-style reimplementation": 3.9470584290102124,
      "Static": 2.9243528842926025e-07
    },
    "detect_wall_s": 4.460103809833527e-06,
    "detector_events": 0,
    "swap_wall_s": 3.026798367500305e-07,
    "whatif_wall_s": {
      "FIR-MINT": 0.0015547447837889194,
      "Full re-tune": 0.0007480205968022346,
      "MINT-style reimplementation": 0.0013375887647271156
    }
  },
  "2": {
    "build_wall_s": {
      "FIR-MINT": 8.41325131431222,
      "Full re-tune": 8.374690252821892,
      "MINT-style reimplementation": 8.415485269855708,
      "Static": 3.5902485251426697e-07
    },
    "detect_wall_s": 4.426110535860062e-06,
    "detector_events": 0,
    "swap_wall_s": 2.9208604246377945e-07,
    "whatif_wall_s": {
      "FIR-MINT": 0.0016172830946743488,
      "Full re-tune": 0.0008347900584340096,
      "MINT-style reimplementation": 0.0013532130979001522
    }
  }
}
```

Hardware: `Linux-5.14.0-687.49.1.el9_8.x86_64-x86_64-with-glibc2.34`; Python `3.11.5`.