# V3 Run Log

## Preparation

- Date: 2026-11-06
- Code: `code_frozen/fir_baselines.py` from the supplied V3 bundle.
- Frozen-code checksum verification: passed (`sha256sum -c SHA256SUMS`).
- V3 checksum recorded in `code_frozen/SHA256SUMS_V3`.
- API check: passed (`API OK`).
- Smoke test: passed with seed `0` and `--skip_sensitivity`; four scenarios and nine policies were produced.

## Dataset regeneration

- COCO 2017 download: downloaded and extracting under `/home/$USER/RAO_OCT/data/coco`.
- Flickr30k: downloaded with KaggleHub under `/home/$USER/RAO_OCT/data/flickr30k`.

## Experiment runs

- T1 synthetic: supplied baseline outputs staged under `runs/baselines_synthetic/`.
- T2 COCO 4-column: not run.
- T2 COCO 4-column baseline job `446857.hpc3-head1.unitn.it`: completed with exit status 0; all gates passed.
- T3 COCO 6-column embedding job `446275.hpc3-head1.unitn.it`: completed successfully; all six columns validated.
- T4 Flickr 4-column embedding job `446271.hpc3-head1.unitn.it`: completed successfully; all four columns validated.
- T3 baseline job `446802.hpc3-head1.unitn.it`: completed with exit status 0.
- T4 baseline job `446801.hpc3-head1.unitn.it`: completed with exit status 0.
- T3 and T4 outputs passed the four-scenario, nine-policy, 36-combination sensitivity checks.
- FIR+detector, Full+detector, and Oracle had zero violation mass in both real-data runs.

## V4 E6 extension campaign

- Date: 2026-11-07
- Code: `code_frozen/fir_extensions.py`; checksum and synthetic smoke test passed before submission.
- Flickr30k 4-column job `455827.hpc3-head1.unitn.it`: exit status 0, wall time 00:01:35.
- COCO 6-column job `455828.hpc3-head1.unitn.it`: exit status 0, wall time 00:03:33.
- COCO 4-column job `455829.hpc3-head1.unitn.it`: exit status 0, wall time 00:01:40.
- Each real-data output passed the four-scenario and four total-time-section checks.
- Each real-data output contains the 12-row fast-path threshold sweep and zero violation mass for all adaptive policy rows.
- Accepted outputs staged under `FINAL_RESULTS/extensions/{flickr4,coco6,coco4,synthetic}/`.
