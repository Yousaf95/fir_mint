# P2a protocol: is the detector needed? Fixed before any P2a run

Recorded 2026-11-08. Brief Part 6.8 (P2a) with the margin confirmed (5%, Reply 1 A5). Tables
(Reply 1, Part 6): COCO-4, COCO-6 and Flickr30k-4 at 30k rows (the draft's tables), and COCO-6 at
full size. Simulator: the frozen v1.0 code (`code_frozen/fir_mint_v4.py`, `fir_baselines.py`,
`fir_extensions.py`), imported unchanged; same scenarios, window streams and estimator as E6.

## Policies

- **FIR-MINT + fast path + ski-rental** (`FIR+fast+SR` of E6, frozen logic): detector with the fast
  path; on a firing, warm-start re-tune and ski-rental switching as in the draft's Algorithm 2.
- **Continuous + ski-rental** (new, the simplest rival, M8): re-tune from the current configuration
  in every window (no detector) on that window's histogram; switch by the same ski-rental rule.
  Reading of "the draft's rule" for a proposal made every window: the rent account belongs to the
  proposal; it is kept while the window's re-tune returns the same proposal and reset when the
  proposal changes (resetting it every window would make the rival unable to ever accumulate rent,
  which is defect M5, not the rival's design). Recall override and the 2-idle-window drop as in
  the draft.
- Reported for context: Static, FIR+detector, Continuous FIR (immediate switch), Oracle.

## Total time

Total = query time (Q_w x estimated cost per window, frozen E6) + build time (frozen build model of
the same table) + **tuner time** = number of tuner invocations x tuner cost per invocation. The
frozen E6 total omits the tuner term. Invocations: FIR+fast+SR, one per detector firing;
Continuous + SR, one per window (30). Tuner cost per invocation, three settings:
(i) 1 ms (the draft's figure); (ii-w) C4 warm re-tune time measured in P3 on the same table
(median over seeds); (ii-c) C4 cold tuning time (excluding the one-time calibration) on the same
table. The same per-invocation cost is charged to both policies.

## Pass condition (per table)

For each Q_w in {1,000; 10,000; 100,000}: per seed, d = mean over the four scenarios of
(FIR total / Continuous total - 1); mean of d over 30 seeds with a bootstrap 95% interval (10,000
resamples). **Pass on a table**: under tuner cost (ii-w), at every Q_w, mean d <= -5% and the
interval's upper end < 0. Settings (i) and (ii-c) and the per-scenario values are reported.
The pilot passes if it passes on every table.

Readings chosen here (to be confirmed by the authors in status report 2): (a) "the P3 tuner cost"
is the warm time, because a running system keeps its plan caches, and the warm cost is the less
favourable one for the detector; (b) the condition must hold at every traffic level, not on
average over them; (c) the rent-account reading for Continuous + SR above.

## Settings

Seeds 0 to 29 (30 workload seeds; brief rule 6.1.3). Label: **estimated** for query time (the
frozen simulator uses calibrated estimators); tuner and build times are measured inputs. Every
table states this.
