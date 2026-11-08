# Provenance corrections

Until commit "Read the git commit at process start", the runners read `git rev-parse HEAD` when they
finished, so a commit made while a job ran was recorded instead of the code that ran. The code
that ran is the commit printed by each PBS job at its start (first line of the job log); it is
listed here and supersedes the `provenance.commit` field of the result file.

| Result file | Recorded | Code that ran (job log) | Same code? |
|---|---|---|---|
| `results/p1/laion_1m_4col/p1.json` (job 466054) | f0a3b16 (public 48fc6eb) | 2eb15db (public 5aa7397) | yes: 48fc6eb changes only WORK_PLAN.md |
| `results/p3/laion_1m_4col/p3.json` (job 467139) | 3b46ca9 | 66a170b | yes: later commits add only the timing-only branch, not executed in this run; mint_c4.py unchanged |
| `results/p3/{coco_30k_4col,coco_30k_6col,flickr_28k_4col}/p3_timing.json` (job 467151) | ca8085c | 92e6abd | yes: ca8085c adds only the P2a files |
| `results/p2a/*/p2a.json` (jobs 467162-467164) | ca8085c | ca8085c | correct |

Public hashes for the rewritten history: `stage2/COMMIT_MAP.md`.
