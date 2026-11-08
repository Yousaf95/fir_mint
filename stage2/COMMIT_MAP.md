# Commit hash map (history rewrite of 8 November 2026)

Before the first push, the local commits after `bb2a2ad` were rewritten to remove the LaTeX
source (`stage1/latex/`), the summary of the authors' Reply 1, and the user name from paths
(replaced by `$USER`). File contents are otherwise unchanged. Hashes named in status report 1
or written into result files map as follows.

| Old (local, not public) | New (public) | Commit |
|---|---|---|
| bb2a2ad | bb2a2ad | Record Stage 1 experiment environment (tag `v1.0-draft`, unchanged) |
| a098c07 | 0708fac | Stage 1: work plan, environment record and number trace |
| 42976e3 | 51e26c8 | Stage 1: compute-node probes, timing-node policy, licence notes |
| f3c758d | 8e27c44 | P1: LAION table preparation and GPU ground truth (prep job 466003 ran here) |
| 2eb15db | 5aa7397 | P1: scale pilot runner and PBS job |
| f0a3b16 | 48fc6eb | Record P1 deviations (P1 job 466054 ran here; `p1.json` provenance says f0a3b16) |
| a6d12e4 | e4f9a5c | P1 result |
| 3395c63 | f80152c | P1b protocol fixed (before any P1b run) |
