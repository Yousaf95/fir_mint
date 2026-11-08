# P1b protocol (amended P1), fixed before any P1b run

Source: Research Brief Reply 1 (Rao Faizan, 8 November 2026), Part 3. Recorded 2026-11-08,
on top of commit a6d12e4 (P1 result). The commit that adds this file fixes the protocol; its
hash goes into status report 2. No P1b run existed when it was committed.

P1 stays recorded as **FAIL** under the brief's original condition (`stage2/P1_REPORT.md`).

## Definitions

- **Informative seed**: a seed on which FIR-MINT's adopted configuration differs from Static's.
- **Noise floor**: in the same job, Static is timed twice, interleaved, on every seed; the floor is
  the largest absolute paired difference between the two Static timings over all seeds, and at
  least 1%. Both numbers (measured maximum and floor used) are reported.

## Pass condition, per table (all four must hold)

1. **Informative seeds.** On every informative seed, FIR-MINT's measured mean latency on the 600
   held-out queries is lower than Static's. The one-sided sign test over the informative seeds is
   reported (p = 0.5^n). At least 5 informative seeds are required. If fewer than 5 appear among
   seeds 0 to 9, seeds 10 to 14 are added once; then the run stops whatever the count.
2. **Non-informative seeds.** On every seed where FIR-MINT kept Static's configuration, the
   absolute paired difference is at most the noise floor.
3. **Interval.** The bootstrap 95% interval (10,000 resamples) of the mean paired difference over
   all seeds excludes zero; marked indicative.
4. **Recall.** FIR-MINT's adopted configuration has minimum over query types of the type-mean
   recall >= 0.90 on the held-out queries on every seed. Full re-tune is a reference, not gated;
   its P1 seed-4 value (0.892) is reported as a result.

The pilot passes when it passes on **both** tables: LAION-1M-4 (`laion_1m_4col`) and COCO-6 at
full size (COCO 2017, about 118,000 rows after de-duplication, the draft's six columns).

## Settings

As in P1: the draft's E1 procedure from the frozen code (`code_frozen/fir_mint_v4.py`, checked
against SHA256SUMS), one abrupt axis-U drift, 600 held-out queries from a pool of 2,000,
exclusive Xeon E5-2680 v4 node (`cpu_type=Xeon2680`, `place=excl`), 28 build threads,
single-threaded search, warm-up round and the median of three interleaved timing rounds.
Seeds 0 to 9 (10 to 14 only under condition 1). The five P1 seeds are reused; their results are
kept and re-run only for the second Static timing. Label: measured.

## Reporting (also for every measured comparison from now on)

Per seed: seed; Static latency; FIR-MINT latency; Full re-tune latency; paired difference (%);
configuration changed (yes/no); indexes built; build seconds (wall clock and CPU-seconds at 28
threads); adopted configuration's minimum type-mean recall and share of queries below 0.90.
Summary: number of informative seeds, sign-test p over them, noise floor, bootstrap interval,
pass or fail per condition.

Reported, not gated:
- **Does the change pay?** Per informative seed: build seconds against the per-window saving
  Q_w x (latency difference), at Q_w in {1,000; 10,000; 100,000}; break-even number of windows.
- **Uncovered mass.** Per seed: share of the post-drift workload on query types whose best plan
  under Static is a partial-cover or merge plan (not a direct index); correlation with the gain.
