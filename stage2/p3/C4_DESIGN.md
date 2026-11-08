# C4: faithful re-implementation of MINT's tuner (for P3)

Source: Zhu et al., "MINT: Multi-Vector Search Index Tuning", ICDE 2026, arXiv 2504.20018v3
(`reference/MINT_2504.20018.pdf`). Section numbers below refer to that paper. MINT's code is not
public; the paper states that Algorithms 1 and 2 suffice to reproduce it (footnote 2).
Requirements from Reply 1: R1 (estimate from single-column indexes and a sample; build only
adopted indexes; calibration time inside tuner cost, build time separate).

## 1. Components as specified by MINT

| Component | MINT (paper) | C4 implementation |
|---|---|---|
| Query | subset of columns; score = sum of per-column scores (Def. 1) | same; equals the draft's mean of per-column cosine up to a constant factor, so rankings agree |
| Plan | (X, EK): ek_i items from each index x_i in a subset of the configuration, union re-ranked (Sec. III-A) | same. Covers the draft's three plan types: direct (one index = q), 2+1 partial cover, merge, and any mix (e.g. x_{1,2} + x_{2,3} for q_{1,2,3}) |
| Cost | cost_idx = x.dim * numDist(q, x, ek) (Eq. 5); cost_rerank = q.dim * sum(ek) (Eq. 6) | same, in distance-computation units; converted to ms by one measured factor per node (reported) for total time |
| numDist model | linear in ek for ek >= 100, fitted per single-column index; multi-column index uses the average slope and intercept across columns (Sec. III-C2) | same model; fitted on the **full** single-column indexes (always in the configuration, brief 6.5), counting FAISS `hnsw_stats.ndis` at ek in a grid; multi-column = mean of the lines. Deviation: MINT fits on indexes over a 1% data sample |
| Recall model | logarithmic in ek, fitted on the training sample with exact ground truth (Fig. 6) | ANN loss per index: fraction of the exact top-ek (by the index's own score) that HNSW returns at search size ek, fitted as a + b ln(ek) on the full single-column indexes; multi-column = mean. Combined with exact coverage (relevant ek): an item ranked j <= ek_x in x is retrieved with probability r_x(ek_x); item recall = 1 - prod_x (1 - r_x(ek_x) 1[j <= ek_x]) |
| Relevant ek | for each ground-truth item of q, its rank in index x_i by the partial score on x_i's columns (Sec. III-C1, Fig. 4) | exact rank over the **full** table for a query sample (100 instances per query, as MINT), by matrix products on CPU; see 2 |
| Planner | |X| <= 3: enumerate the (k+1)^|X| relevant-ek combinations; else Algorithm 1 (DP over subsets of a ground-truth sample of k' items, several samples) | same; k' = 5 (paper default); samples = 4 (paper says "several"; swept in P3) |
| Recall target | recall@k >= theta; paper's experiments use recall@100, theta 0.90 (semi-synthetic) / 0.97 (real) | k = 10, theta = 0.90 for our settings; MINT's settings (k = 100) for the faithfulness check |
| Searcher | Algorithm 2 beam search: candidates per query = subsets x with x.vid ⊆ q.vid and |x.vid| >= |q.vid| - di; seeds = subsets of Cand(q) with <= se indexes; keep b best feasible; add one index per iteration, drop unused indexes; stop when improvement <= im; return best ever | same; di = 2, se = 2, im = 5% (paper defaults); b = 5 default, sweep {3, 5, 10} (brief C4) |
| Caching | plan cache keyed on (q, X'_q) where X'_q = indexes useful to q; relevant-ek cache per (q, x) (Sec. IV-B) | same; cache hits and misses counted |
| Storage | number of indexes (graph only, vectors not duplicated) (Sec. II-B, V-A) | **deviation**: our indexes are FAISS IndexHNSWFlat, which stores the concatenated vectors. Storage in bytes = rows x (4 x dim + 4 x 2M) per index; the budget is stated in bytes (brief Part 6.3). For the faithfulness check we also run MINT's unit (number of indexes) |
| Training sample | 1% of the data and historical queries; training time 3-32 s (Sec. III-C2) | no data sample; query sample = 100 held-out training rows per query type (disjoint from the 600 test queries' pool) |

## 2. Ranks at full size (deviation from MINT, decided before any run)

MINT computes ground truth and fits its models on a 1% data sample (Sec. III-C2) but does not say
how sample ranks map to full-size ek. They cannot be mapped by scaling: the sample's top-k items
are not the full table's top-k, and a scaled sample rank of the top item is about N / n (100 at 1%),
whereas a direct index needs ek of about k. C4 therefore computes, for each query instance in the
training sample, the exact full-table ground truth and each item's exact rank under every
candidate index's partial score. This uses only the stored column vectors (matrix products), no
multi-column index, so R1 holds. Its cost grows linearly with the rows and is part of calibration
time. The numDist and recall models are fitted on the full single-column indexes, which every
configuration contains (brief 6.5). Both deviations are reported with the P3 result.

Execution semantics that the estimates assume (and that measured runs must use): index x searched
with k = ek and efSearch = max(ek, 100), the lower end of MINT's linear regime; union re-ranked
by the exact full score.

## 2b. Two corrections found in the smoke test (Flickr30k 28k, login node, 2026-11-08)

1. numDist: MINT's single line over ek in [100, 3200] overestimated the measured distance count at
   ek = 100 by 69% to 78% on all four Flickr columns (FAISS `hnsw_stats.ndis`), which penalised
   direct plans (small ek) against merges. C4 uses piecewise-linear interpolation through the
   measured points (linear between grid points, linear extrapolation past 3200). The single line's
   error at every grid point is stored and reported (`Calibration.line_fit`).
2. Planner monotonicity: Algorithm 1's candidates, evaluated on all instances, could be worse than
   not using an added index (adding the direct index of a 3-column query raised the estimated plan
   cost from 3.05M to 4.75M units). For |X_q| > 3 the candidate set now also contains the best plan
   of every subset of X_q with one index fewer (cached, recursive), so adding an index never makes
   a plan worse.

## 3. Measurements for P3

- Tuner wall-clock time, split into (a) one-time training (sample indexes, numDist and recall fits,
  sample ground truth) and (b) index tuning (Algorithm 2 with the planner), cold and warm.
- Warm start (C4 extension, not in MINT): beam seeded with the current configuration, plan and
  relevant-ek caches kept across windows. Measured on the drifted workload after tuning the
  stable one.
- Build time of the adopted indexes, separately (R1).
- What-if calls (planner calls that miss the cache) as a secondary count.
- Faithfulness (P3 pass condition, factor 3): MINT's workload construction on LAION-1M-4
  (queries with each column chosen independently with p = 0.5, weights Uniform(0,1) normalised,
  6 to 8 queries, recall@100), tuning time against MINT Fig. 14 (about 85-185 s for 10-16
  queries on 1M rows, read from the plot) at matched number of queries; the data and hardware
  differ, which the report states. We also scale to 10, 12, 14, 16 queries to compare the slope.
- Quality check of C4 against v1.0's greedy tuner on the same estimator inputs: configuration,
  estimated cost, and measured latency of both on the drifted workload.

## 4. Open choices (defaults, reported, swept where cheap)

| Choice | Default | Sweep |
|---|---|---|
| beam width b | 5 | 3, 5, 10 |
| ground-truth samples for DP | 4 of k' = 5 items | 1, 4, 8 |
| ek grid for numDist and recall fits | 100, 200, 400, 800, 1600, 3200 | none |
| candidate ek per index (enumeration, \|X_q\| <= 3) | 0 and the pooled ranks at quantiles 0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95, 0.97, 0.99, 1.0 | none |
| DP (\|X_q\| > 3) | Algorithm 1 per sampled k' = 5 items of one instance; candidate EK from each sample, evaluated on all instances; cheapest feasible kept | none |
| one query type = one MINT query | weight = histogram mass; query vectors = training rows | none |
