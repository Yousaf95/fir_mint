# FIR-MINT work plan (task A of the Research Brief, Part 1)

Date: 2026-11-08. Prepared by: Claude Code (Opus 5.5) with H. M. Yousaf.
Repository: `/home/$USER/RAO_OCT`, HEAD `bb2a2ad`.
Compute times below are planning estimates, not measurements. They are
replaced by measured values as each run finishes.

## What already exists (checked 2026-11-08)

| Item | Where | Use in the plan |
|---|---|---|
| Frozen v1.0 code with checksums | `code_frozen/` (`SHA256SUMS`, `_V3`, `_V4`) | Stage 1 trace; the simulator for P2a |
| E1 + E3 per-seed results (COCO-6, Flickr30k-4) | `FINAL_RESULTS/{coco6,flickr4}/results.json` | Trace Tables II, III |
| COCO-4 results (CPU and H100 hosts) | `results/`, `fir_mint_v4_results_coco_30k_4col_gpu/`, `EXPERIMENT_RESULTS_ALL.md` | Trace Tables II, III |
| E4 baselines, E5 sensitivity | `FINAL_RESULTS/baselines/*/baselines.json` | Trace Table IV, Sec. VII-E |
| E6 fast path and total time | `FINAL_RESULTS/extensions/*/extensions.json` | Trace Table V, Fig. 6 |
| E2 synthetic scalability | `runs/synthetic/`, `runs/extensions_synthetic.json` | Trace Fig. 5, Sec. VII-C |
| Rejected 8-column run and its table | `FINAL_RESULTS/rejected_runs/coco8/`, `embeddings/coco_30k_8col/` | P4 input (no request to the authors needed) |
| 8-column diagnosis (pool x efSearch sweep, 3 seeds) | `runs/diagnose_coco8/diagnosis.json` | P4 starting point |
| MINT-style pilot on Flickr30k (greedy, about 1 ms per tune) | `runs/pilot_mint_flickr/` | Not a faithful MINT; does not count for P3 |
| LaTeX source of the draft | not in the repository | Needed for Stage 1 and Stage 5 |

## Stage 1: Prepare (about 1 week)

1. Complete `env.json` to the schema of Part 6.2. CPU, RAM, OS and library
   versions are recorded from the login node. The compute-node CPU, GPU, RAM
   and frequency scaling come from a short PBS probe job on `commonCPUQ` and
   `commonGPUQ` (`stage1/probe_node.pbs`, under 5 min each).
2. Trace table: every number in the abstract, Sections VII and VIII and
   Tables II to V against the result files above. Output
   `stage1/trace_table.csv` (number, place in draft, source file, field,
   recomputed value, match or mismatch) and a script that rebuilds it
   (`stage1/trace.py`). Settles the 21 items of Part 3.2, including #10 and
   #21, which need the per-seed data.
3. Define the recall measure used in v1.0. The E1 field `min_recall` (for
   example 0.99268 = 407/410) is not a multiple of 0.1, so it is not a
   per-query minimum (M4). The trace states what it is.
4. Data pipelines, prepared but not yet run at scale:
   - MINT News (0.1M rows, 4 columns): download from the MINT artifact
     link and record its terms (stop point 5 if the terms are unclear).
   - LAION-400M embeddings: 1 to 2 shards (about 1M rows each), `img_emb` and
     `text_emb`, held-out query rows, de-duplication. Needs `pyarrow`.
   - Ground truth on GPU with PyTorch matmul. The installed FAISS is the CPU
     build (`faiss-cpu 1.15.1`), with no GPU support.
5. Freeze v1.0 as a tagged commit (`v1.0-draft`), with the result files it
   used.

Deliverable: Stage 1 status report (Part 8.2), trace table, env.json, memory
and disk plan.

## Stage 2: the four pilots (about 4 to 8 weeks; most of it is P3 and P2b code)

| Pilot | Runs | Scripts | Estimated compute |
|---|---|---|---|
| P1 Scale | News 0.1M x 4 col, then LAION 1M x 2 col; abrupt axis-U drift; Static and re-tuned; 5 seeds; build time, memory, flat scan per query type, held-out recall, latency on 600 queries | `pilots/p1_scale.py`, `p1_*.pbs` | News: about 1 h per seed (14 candidate indexes, up to 2,048-d concatenations). LAION 1M: 2 to 4 h per seed for HNSW builds with 8 threads. About 1 day of queue time in total |
| P3 Tuner cost | MINT beam search (b in {3,5,10}) + DP planner from the ICDE paper; cold and warm; News 0.1M and LAION 1M; 5 repetitions; also MINT's own workloads to compare with its Fig. 14 | `fir_mint2/tuner_mint.py`, `pilots/p3_tuner.py` | Coding: 1 to 2 weeks. Runs: a few hours, mostly calibration |
| P2a Detector value | In the frozen simulator, add "Continuous + ski-rental, no detector"; 30 seeds x 4 scenarios x Q_w in {1e3,1e4,1e5}; tuner cost 1 ms and the P3 cold and warm values on the same table | `pilots/p2a_detector.py` | Minutes per dataset on CPU |
| P4 Recall | Re-run the 8-column diagnosis with held-out per-query recall by query type, Static included; theta sweep 0.80 to 0.99 on News with per-plan search effort | `pilots/p4_recall.py` | A few hours |
| P2b Config vs per-query | News: axis-U and axis-Q scenarios; (a) Static + LAET, (b) re-tuned, (c) re-tuned + LAET, at equal recall | `baselines/laet.py`, `pilots/p2b.py` | Coding LAET: about 1 week (needs `lightgbm`). Runs: hours |

Order (Part 6.8): P1, then P3, then P2a; P4 and P2b in parallel. Then stop
for the authors' decision (stop point 3).

## Stages 3 to 6 (after the decision; outline only)

- Stage 3 (3 to 4 weeks): complete C4, implement C2 (per-index accounts with
  carry-over) and C1 or C3; proof document; Sections III and IV.
- Stage 4 (4 to 6 weeks): E1 to E12, ablations, drift runbooks. The 10M runs
  need storage outside `/home` (see the open questions).
- Stage 5 (3 weeks): rewrite, with every number generated by a script.
- Stage 6 (2 weeks): fact and citation check, independent review, template.

## Decisions recorded

- 2026-11-08, H. M. Yousaf: the "proposed" margins of Part 6.8 are confirmed
  as written. From now on they are fixed (Part 1, rule 3).
- 2026-11-08, H. M. Yousaf: compute nodes obtained through PBS are exclusive
  for timing runs.
- 2026-11-08: LaTeX source received (`FIR-MINT_ICDE_latex_humanized.zip`),
  extracted to `stage1/latex/`.
- Still open: storage for the 10M tables (question 3).
- 2026-11-08, probe jobs 465945, 465946, 465959 (`stage1/probe/`): a plain
  `ncpus=8` request on `commonCPUQ` is NOT exclusive (node load 47.6 on 96
  cores), and the queue mixes CPU types (Xeon2680 28-core 314 GB; Xeon5118;
  Xeon6252N 96-core 0.5 to 1.3 TB). v1.0 timings did not pin either.
  Default from now on, for every measured run (builds and queries on the same
  node): `-l select=1:ncpus=28:mem=300gb:cpu_type=Xeon2680 -l place=excl`
  (5 of 6 nodes free at probe time). The 10M runs of Stage 4 use exclusive
  Xeon6252N nodes. The GPU node (2 x H100 NVL, 503 GB) is used for ground
  truth only, so its sharing does not affect timings.
- 2026-11-08: MINT News embeddings come from `RealTimeData/bbc_news_alltime`
  on Hugging Face, which declares no licence; MINT's README defers to the
  original owners. Stop point 5: not downloaded until the authors decide.
  LAION-400M: metadata released under CC-BY 4.0 (laion.ai blog); the brief
  treats the released `img_emb`/`text_emb` as usable. Shards 0 and 1
  downloaded to `data/laion/` with checksums.

## Reply 1 (Rao Faizan, 8 November 2026)

Decisions D1-D3, accepted deviations A1-A5 and requirements R1-R6 are listed in
`stage2/REPLY1_CHANGES.md`; the amended P1 condition is `stage2/P1b_PROTOCOL.md`. Run order
from now on: P3, P2a, P4, P2b, P1b. Status report 2 after P3 and P2a. MINT News on hold (D2);
second pilot table is COCO-6 at full size.

## Deviations from the brief

- P1 table: LAION 1M with **4 columns**, not 2. Reasons: (a) the v1.0
  estimator needs at least 3 columns (it calibrates 3-column types and
  hardcodes columns 0, 1, 2); (b) with 2 columns the only optional index is
  {I, T}, which Static already builds under the 8-unit budget, so Static and
  the re-tuned configuration would coincide and P1 could not show a gain.
  Columns: I_b32 and T_b32 (LAION release), T_b16 (CLIP ViT-B/16) and T_lb32
  (OpenCLIP ViT-B/32 LAION-2B) on the same captions; the last two are added by
  us (brief Part 6.3 allows this). This table also replaces News in P1 while
  the News licence is open.
- P1 builds use 28 threads (exclusive 28-core node); v1.0 used 8. Search stays
  single-threaded.
- Recall in P1 uses exact ground truth precomputed on GPU; the run checks it
  against v1.0's `recall_of` on 24 real plans and aborts on any difference.
- v1.0 calibrates its estimators from live timings, so configurations depend
  on the host. Flickr30k seed 0 rerun on the login node: FIR-MINT and Full
  configurations equal the v1.0 log, Static differs.

## Open questions for the authors

Items marked [decision] need a human decision before the stage named.

1. [decision, before Stage 2] Confirm or change the "proposed" margins of
   Part 6.8: P1 sign test plus an indicative interval; P2a at least 5% with an
   interval excluding zero; P2b at least 10%; P3 within a factor of 3 of MINT
   and a warm-start cut of at least 30%; C3 1% violation at 95%.
2. [decision, before Stage 2] Hardware for the pilots: `commonCPUQ` nodes
   (8 CPUs, 64 GB requested so far) and an H100 on `commonGPUQ`. Can we get
   an exclusive node for timing runs, and is a large-memory node available
   for Stage 4?
3. [decision, before Stage 4] Disk: the home quota is 240 GB with 188 GB
   used, so about 52 GB is free. The 1M pilots fit. The 10M tables do not.
   Options: a project or scratch area that both CPU and GPU nodes can see
   (GPU nodes cannot read `/data`), or removing `data/coco/*.zip`
   (already extracted) after the authors agree.
4. The LaTeX source of v1.0 is not in the repository. Please share it for
   Stage 1 (number trace) and Stage 5.
5. [decision] Licences: MINT data terms and use of LAION embeddings
   (stop point 5) once checked.
6. The Git history shows GitHub Copilot as co-author on recent commits. Record
   this for the AI-use statement (default 9 of Part 8.4).
- 2026-11-08: frozen-code check. All Python files in `code_frozen/` match `SHA256SUMS`
  (and `_V3`, `_V4`). Four PBS scripts (`embed_multi_gpu.pbs`, `run_coco6_cpu.pbs`,
  `run_coco8_cpu.pbs`, `run_hpc4ds_gpu.pbs`) do not: commit 805ec36 replaced the user name
  by `$USER` in them after the checksums were taken. Jobs now check only the files they run.
