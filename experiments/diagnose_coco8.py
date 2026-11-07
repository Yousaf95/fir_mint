"""Small COCO 8-column diagnosis for recall, pools, ties, and duplicates."""
import argparse
import json
import platform
import time
from pathlib import Path

import numpy as np

import fir_mint_v4 as F


def duplicate_rates(data):
    return {
        str(index): float(1.0 - np.unique(column, axis=0).shape[0] / len(column))
        for index, column in enumerate(data)
    }


def run_seed(seed, data, C, pools, ef_search, queries_per_signature):
    rng = np.random.default_rng(seed)
    results = []
    signatures = ((1, 1), (1, 1, 1), (2, 1))
    for signature in signatures:
        width = 3 if signature == (2, 1) else len(signature)
        query_types = [
            tuple(sorted(rng.choice(C, size=width, replace=False).tolist()))
            for _ in range(queries_per_signature)
        ]
        for query in query_types:
            query_vector = F.make_query(data, query, rng)
            for pool in pools:
                parts = (
                    [(column,) for column in query]
                    if signature != (2, 1)
                    else [query[:2], query[2:]]
                )
                F.EF_SEARCH = ef_search
                recall = F.recall_of(
                    F.get_store(data),
                    query,
                    ("merge", parts, pool),
                    query_vector,
                )
                results.append(
                    {
                        "seed": seed,
                        "signature": signature,
                        "query": query,
                        "pool": pool,
                        "ef_search": ef_search,
                        "recall": recall,
                    }
                )
    for width in (1, 2, 3):
        for _ in range(queries_per_signature):
            query = tuple(sorted(rng.choice(C, size=width, replace=False).tolist()))
            query_vector = F.make_query(data, query, rng)
            scores = F.joint(data, query, query_vector)
            boundary = np.partition(scores, -F.TOP_K)[-F.TOP_K]
            ties = int(np.count_nonzero(np.isclose(scores, boundary, rtol=1e-6, atol=1e-6)))
            F.EF_SEARCH = ef_search
            recall = F.recall_of(
                F.get_store(data), query, ("exact", None, None), query_vector
            )
            results.append(
                {
                    "seed": seed,
                    "signature": ("exact", width),
                    "query": query,
                    "pool": None,
                    "ef_search": ef_search,
                    "recall": recall,
                    "boundary_ties": ties,
                }
            )
    return results, duplicate_rates(data)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True)
    parser.add_argument("--seeds", nargs="+", type=int, default=[0, 1, 2])
    parser.add_argument(
        "--pools", nargs="+", type=int, default=[40, 80, 160, 320, 640, 1280, 2560, 5120]
    )
    parser.add_argument("--ef-search", nargs="+", type=int, default=[256, 512, 1024])
    parser.add_argument("--queries-per-signature", type=int, default=10)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    C = F.load_real(args.data)
    data = F.REAL
    start = time.perf_counter()
    results = []
    duplicates = None
    for seed in args.seeds:
        for ef_search in args.ef_search:
            rows, duplicates = run_seed(
                seed, data, C, args.pools, ef_search, args.queries_per_signature
            )
            results.extend(rows)
    summary = []
    for signature in ((1, 1), (1, 1, 1), (2, 1)):
        for pool in args.pools:
            for ef_search in args.ef_search:
                values = [
                    row["recall"]
                    for row in results
                    if tuple(row["signature"]) == signature
                    and row["pool"] == pool
                    and row["ef_search"] == ef_search
                ]
                summary.append(
                    {
                        "signature": signature,
                        "pool": pool,
                        "ef_search": ef_search,
                        "min_recall": min(values),
                        "mean_recall": float(np.mean(values)),
                        "pass": min(values) >= F.RECALL_TARGET,
                    }
                )
    for width in (1, 2, 3):
        for ef_search in args.ef_search:
            values = [
                row["recall"]
                for row in results
                if tuple(row["signature"]) == ("exact", width)
                and row["ef_search"] == ef_search
            ]
            ties = [
                row["boundary_ties"]
                for row in results
                if tuple(row["signature"]) == ("exact", width)
                and row["ef_search"] == ef_search
            ]
            summary.append(
                {
                    "signature": ("exact", width),
                    "pool": None,
                    "ef_search": ef_search,
                    "min_recall": min(values),
                    "mean_recall": float(np.mean(values)),
                    "mean_boundary_ties": float(np.mean(ties)),
                    "max_boundary_ties": max(ties),
                    "pass": min(values) >= F.RECALL_TARGET,
                }
            )
    output = {
        "settings": {
            "seeds": args.seeds,
            "pools": args.pools,
            "ef_search": args.ef_search,
            "queries_per_signature": args.queries_per_signature,
            "recall_target": F.RECALL_TARGET,
        },
        "duplicates": duplicates,
        "summary": summary,
        "elapsed_s": time.perf_counter() - start,
        "hardware": platform.platform(),
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps({"duplicates": duplicates, "summary": summary}, indent=2))


if __name__ == "__main__":
    main()
