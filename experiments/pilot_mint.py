"""Pilot comparison for a MINT-style reimplementation.

This is new experiment code and does not modify the frozen FIR-MINT sources.
The MINT-style baseline follows the same planner/cost model but performs a
from-scratch marginal-gain search over all candidates. It is not the authors'
original implementation.
"""
import argparse
import json
import platform
import sys
import time
from pathlib import Path

import numpy as np

import fir_mint_v4 as F


POLICIES = ("Static", "FIR-MINT", "Full re-tune", "MINT-style reimplementation")


def mint_style_retune(est, dist):
    """Run an independent MINT-style from-scratch marginal-gain search."""
    est.calls, est.cache = 0, {}
    cfg = frozenset()
    best = est.score(dist, cfg)
    while True:
        candidates = F.candidate_universe(dist)
        trials = []
        for candidate in candidates:
            if candidate in cfg or F.storage(cfg | {candidate}) > F.EXTRA_BUDGET:
                continue
            before = est.score(dist, cfg)
            after = est.score(dist, cfg | {candidate})
            gain = (before[0] - after[0]) * 10.0 + (before[1] - after[1])
            if gain > 0:
                trials.append((gain / len(candidate), after, candidate))
        if not trials:
            break
        _, score, candidate = max(trials, key=lambda item: (item[0], -item[1][1]))
        if score >= best:
            break
        cfg = cfg | {candidate}
        best = score
    return cfg, est.calls


def timed_estimator_score(est, dist, cfg):
    est.calls, est.cache = 0, {}
    start = time.perf_counter()
    score = est.score(dist, cfg)
    return score, est.calls, time.perf_counter() - start


def measure_latency(store, plans, queries, query_vectors):
    for _ in range(1):
        for plan, query, query_vector in zip(plans, queries, query_vectors):
            F.run_plan(store, plan, query, query_vector)
    measurements = []
    for _ in range(3):
        start = time.perf_counter()
        for plan, query, query_vector in zip(plans, queries, query_vectors):
            F.run_plan(store, plan, query, query_vector)
        measurements.append((time.perf_counter() - start) * 1000 / len(plans))
    return float(np.median(measurements)), float(np.percentile(measurements, 95))


def run_seed(seed, data_folder):
    rng = np.random.default_rng(seed)
    C = F.load_real(data_folder)
    store = F.get_store(F.REAL)
    est = F.Estimator(store, rng, n=80)
    p0 = F.zipf_dist(C, rng, single_mass=0.85)
    p1 = F.zipf_dist(C, rng, single_mass=0.35)
    initial, _, _, _ = F.full_retune(est, F.sample_window(p0, rng))
    observed = F.sample_window(p1, rng)

    start = time.perf_counter()
    fir, _, fir_calls, fir_tune = F.fir_retune(est, observed, initial)
    fir_tune_wall = time.perf_counter() - start
    start = time.perf_counter()
    full, _, full_calls, full_tune = F.full_retune(est, observed)
    full_tune_wall = time.perf_counter() - start
    start = time.perf_counter()
    mint, mint_calls = mint_style_retune(est, observed)
    mint_tune_wall = time.perf_counter() - start

    query_keys = list(p1)
    query_indices = rng.choice(len(p1), size=600, p=[p1[q] for q in p1])
    queries = [query_keys[index] for index in query_indices]
    query_vectors = [F.make_query(F.REAL, query, rng) for query in queries]
    configs = {
        "Static": initial,
        "FIR-MINT": fir,
        "Full re-tune": full,
        "MINT-style reimplementation": mint,
    }

    rows = []
    for policy, cfg in configs.items():
        new_indexes = sorted(cfg - initial)
        build_store = F.Store(F.REAL)
        build_start = time.perf_counter()
        for index in new_indexes:
            build_store.get(index)
        build_wall = time.perf_counter() - build_start
        plans = [est.best_plan(query, cfg)[0] for query in queries]
        swap_start = time.perf_counter()
        active_config = cfg
        swap_wall = time.perf_counter() - swap_start
        latency, p95 = measure_latency(store, plans, queries, query_vectors)
        recalls = [
            F.recall_of(store, query, plan, query_vector)
            for query, plan, query_vector in zip(queries, plans, query_vectors)
        ]
        rows.append(
            {
                "seed": seed,
                "policy": policy,
                "latency_ms": latency,
                "p95_ms": p95,
                "min_recall": float(min(recalls)),
                "mean_recall": float(np.mean(recalls)),
                "recall_gate_pass": bool(min(recalls) >= F.RECALL_TARGET),
                "whatif_calls": 0,
                "tuning_wall_s": 0.0,
                "build_wall_s": build_wall,
                "swap_wall_s": swap_wall,
                "new_indexes": len(new_indexes),
                "config": [list(index) for index in sorted(cfg)],
            }
        )

    rows[1]["whatif_calls"], rows[1]["tuning_wall_s"] = fir_calls, fir_tune_wall
    rows[2]["whatif_calls"], rows[2]["tuning_wall_s"] = full_calls, full_tune_wall
    rows[3]["whatif_calls"], rows[3]["tuning_wall_s"] = mint_calls, mint_tune_wall

    reference = F.sample_window(p0, np.random.default_rng([seed, 90]))
    windows = [F.sample_window(p1, np.random.default_rng([seed, 91])) for _ in range(2)]
    detector = F.Detector(reference, np.random.default_rng([seed, 92]))
    detect_wall = 0.0
    detected = 0
    for window in windows:
        start = time.perf_counter()
        pooled = detector.observe(window)
        detect_wall += time.perf_counter() - start
        detected += pooled is not None
    timing = {
        "detect_wall_s": detect_wall,
        "whatif_wall_s": {
            "FIR-MINT": fir_tune_wall,
            "Full re-tune": full_tune_wall,
            "MINT-style reimplementation": mint_tune_wall,
        },
        "build_wall_s": {row["policy"]: row["build_wall_s"] for row in rows},
        "swap_wall_s": float(np.mean([row["swap_wall_s"] for row in rows])),
        "detector_events": detected,
    }
    return rows, timing


def write_report(results, timings, out, data_folder):
    gate = all(row["recall_gate_pass"] for row in results)
    lines = [
        "# MINT pilot",
        "",
        "This pilot uses a MINT-style reimplementation, not the original MINT code.",
        "It shares the frozen FIR-MINT estimator, FAISS settings, recall target, and data.",
        f"Dataset: `{Path(data_folder).name}`; seeds: {sorted({r['seed'] for r in results})}.",
        f"Recall gate (minimum empirical recall >= {F.RECALL_TARGET:.2f}): "
        f"**{'PASS' if gate else 'FAIL'}**.",
        "",
        "| Seed | Policy | Latency ms | p95 ms | Min recall | Gate | What-if calls | Tuning s | Build s | New indexes |",
        "|---:|---|---:|---:|---:|---|---:|---:|---:|---:|",
    ]
    for row in results:
        lines.append(
            f"| {row['seed']} | {row['policy']} | {row['latency_ms']:.3f} | "
            f"{row['p95_ms']:.3f} | {row['min_recall']:.3f} | "
            f"{'PASS' if row['recall_gate_pass'] else 'FAIL'} | {row['whatif_calls']} | "
            f"{row['tuning_wall_s']:.4f} | {row['build_wall_s']:.4f} | {row['new_indexes']} |"
        )
    lines += [
        "",
        "## Timing decomposition",
        "",
        "Recall-estimation/tuning wall time is reported separately from query latency.",
        "",
        "```json",
        json.dumps(timings, indent=2, sort_keys=True),
        "```",
        "",
        f"Hardware: `{platform.platform()}`; Python `{sys.version.split()[0]}`.",
    ]
    out.mkdir(parents=True, exist_ok=True)
    (out / "pilot.md").write_text("\n".join(lines), encoding="utf-8")
    (out / "pilot.json").write_text(
        json.dumps({"results": results, "timings": timings}, indent=2),
        encoding="utf-8",
    )
    return gate


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True)
    parser.add_argument("--seeds", nargs="+", type=int, default=[0, 1, 2])
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    F.REAL = F.REAL_Q = None
    results, timings = [], {}
    for seed in args.seeds:
        rows, seed_timing = run_seed(seed, args.data)
        results.extend(rows)
        timings[str(seed)] = seed_timing
        print(f"seed {seed} complete")
    gate = write_report(results, timings, Path(args.out), args.data)
    print(f"recall gate: {'PASS' if gate else 'FAIL'}")
    if not gate:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
