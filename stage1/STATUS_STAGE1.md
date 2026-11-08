# FIR-MINT status report

Stage: 1 (Prepare). Date: 2026-11-08. Prepared by: Claude Code (Opus 5.5) with H. M. Yousaf.
Commit: not yet frozen (working tree on top of `bb2a2ad`; a frozen commit follows the authors' go-ahead).

## 1. What was done

- Work plan: `WORK_PLAN.md`.
- Environment: `env.json` completed to the schema of Part 6.2, except the compute-node probe (open item 5.1).
- LaTeX source of v1.0 received and unpacked: `stage1/latex/`.
- Number trace of draft v1.0: `stage1/trace.py` regenerates `stage1/trace_table.csv` and
  `stage1/trace_report.md` from the result files. It covers Tables II to V, every number in the
  text of Section VII, the abstract, the introduction and the method text.
- Recall measure of v1.0 identified in code (`code_frozen/fir_mint_v4.py`, lines 439-448).
- Duplicate result copies checked: `runs/*` and `FINAL_RESULTS/*` are byte-identical.

## 2. Results against the pass conditions

Stage 1 has no pass conditions. Stop-and-ask point 1 (a headline number that cannot be traced)
is **not triggered**: every number in the draft traces to a result file.

| Trace outcome | Count |
|---|---:|
| Numbers checked | 305 |
| Match at printed precision | 291 |
| Mismatch | 4 |
| Information rows (context, no printed value) | 10 |
| Not traceable | 0 |

The four mismatched rows are three printed numbers (a range counts as two rows):

| Place | Printed | Recomputed | Source |
|---|---:|---:|---|
| Table II, Synthetic-4, Static latency | 0.633 | 0.6336 (truncated, not rounded) | `runs/synthetic/fir_mint_v4_results/results.json` |
| VII-D, "Continuous buys 1 to 9 points" | 1 to 9 | -0.09 to 8.35 | `FINAL_RESULTS/baselines/*/baselines.json` |
| VII-G, fast path reduces regret "by up to 40%" | 40 | 60.0 (from Table V: 0.5 to 0.2) | Table V, `FINAL_RESULTS/extensions/*` |

Two further claims match only when restricted to real data (finding 4 below).

## 3. Findings that change the paper or the pilots

1. **The draft's recall measure.** `min_recall` is the minimum over query types of the
   *mean* per-query recall of that type, measured on 600 held-out queries. The "Min recall"
   column of Table II is the **mean over seeds** of FIR-MINT's value. Violating mass counts a
   type only when its mean is below 0.90. Neither is a per-query guarantee (M4).
2. **Recall binds on real data.** COCO-6, seed 2: Static has per-type mean recall 0.850 with
   violating mass 0.0048. Full re-tune is at exactly 0.900. FIR-MINT is at 0.925. Table II
   reports only the seed mean of FIR-MINT (0.969). Source: `FINAL_RESULTS/coco6/results.json`.
3. **Per-query recall is lower.** In the MINT-style pilot on Flickr30k (`runs/pilot_mint_flickr/pilot.md`),
   the per-query minimum is 0.7 to 0.8 on seeds 0 and 1 for every policy, Static included.
   "Always met" holds only for per-type means on the accepted runs.
4. **VII-F total-time claims hold on the three real datasets only.** On Synthetic-5,
   FIR+fast+SR is 11.4% worse than the default in one cell (claim: at most 3.8%) and 1.3 points
   from the best mean (claim: 1.1). Fig. 6 shows only real data; the text says "every dataset".
5. **Table III mislabel (review item 20).** The row "Synthetic-5" matches the 4-column synthetic
   file exactly (`runs/synthetic/fir_mint_v4_results/results.json`, C = 4). The 5-column
   synthetic data is used only in Tables IV and V.
6. **Separate runs, separate calibrations (review items 10 and 14).** E3 (Table III) and E4
   (Table IV) are different runs. For COCO-6 new type, the paired FIR-vs-Static change is
   -30.9% in the E3 run and -45.0% in the E4 run; the ratio of Table IV means gives -53.4%.
   Mean detection delay is 1.40 to 1.45 windows in the E3 run and 1.50 to 1.55 in the E4 run.
7. **"Up to 2.5x" in the introduction** is the mean over 5 seeds of Static/Oracle for COCO-6 new
   type (2.51x). Per seed it ranges from 1.18x to 4.78x.
8. **Review item 21 is answered.** On the COCO-4 CPU host, FIR-MINT built 1 new index on seeds 1
   and 4 and measured +2.2% and +3.6% against Static. On the H100 host the same seeds gave
   -13.8% and -20.0%. The configurations changed, so "the workloads happen to suit the initial
   configuration" is not supported; CPU-host timing noise is the likelier cause.

## 4. Status of the 21 items of Part 3.2

| # | Status after the trace |
|---|---|
| 1, 2 | Both ranges trace. 8-29x and 3-20x are Continuous FIR vs FIR in the E4 run; 8-27x and 3.6-30x are "Full every window" vs FIR in the E3 run. Two baselines; the text must name them. |
| 3 | Both ranges trace (measured -3.0 to +5.1, estimated -2.3 to +1.0). "About 2%" is not supported by the measured range. |
| 4 | Confirmed; see findings 1 to 3. |
| 5 | Confirmed: 60%, not 40%. |
| 6 | Confirmed: -0.1 to +8.3 points. |
| 7 | -2 to +6 traces to the E3 baseline; +7.7 is the E4 baseline. Partly accepted, as in the review. |
| 9 | E5 ranges trace (range over the 9 detector settings). They come from the E5 run, so they differ from Tables IV and V. |
| 10 | Resolved: finding 6. |
| 11 | 67% traces (COCO-6 new type, Q_w = 100,000, total time). |
| 14 | Confirmed: finding 6. |
| 20 | Resolved: finding 5. |
| 21 | Resolved: finding 8. |
| 8, 12, 13, 15 to 19 | Text and algorithm items; no number to trace. They are fixed in Stage 5. |

## 5. Numbers to carry into the paper

None yet. v1.0 numbers are replaced by Stage 2 and Stage 4 results.

## 6. Deviations from the brief

- The brief asks for a 95% interval on every number. Stage 1 recomputes the draft's own
  t-intervals; bootstrap intervals start with the new runs.
- The frozen commit of v1.0 is not yet made (waiting for the authors' go-ahead to commit).

## 7. Problems and open questions

1. Compute-node probe (CPU model, frequency scaling, GPU) not yet run. It needs a short PBS job.
2. [decision] Storage for the 10M tables (about 52 GB free in `/home`). Not needed before Stage 4.
3. [decision] MINT data terms and LAION licence, checked when the data are downloaded (stop point 5).

## 8. Next step proposed

Stop-and-ask point 2 is cleared except the compute-node probe: margins confirmed, nodes exclusive,
pilot tables at the default (News, then LAION 1M). Next: run the probe job, download MINT News,
then P1 on News (0.1M rows, 4 columns, 5 seeds), then P3.
