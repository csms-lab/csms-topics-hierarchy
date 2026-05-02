#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import json
import re
import unicodedata
from pathlib import Path

import networkx as nx


GENERIC_SUFFIXES = {
    "algorithm",
    "algorithms",
    "application",
    "applications",
    "formulation",
    "formulations",
    "method",
    "methods",
    "policies",
    "policy",
}


def parse_args() -> argparse.Namespace:
    here = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(
        description="Derive topic paper counts and edge overlap weights from a mined local corpus."
    )
    parser.add_argument(
        "--graph",
        type=Path,
        default=here / "topics.graphml",
        help="Input GraphML file to enrich in place.",
    )
    parser.add_argument(
        "--corpus-json",
        type=Path,
        default=here.parent / "library_topic_mining.json",
        help="Path to the mined local library JSON file.",
    )
    parser.add_argument(
        "--topic-stats",
        type=Path,
        default=here / "topic-corpus-stats.tsv",
        help="Output TSV for per-topic corpus counts.",
    )
    parser.add_argument(
        "--edge-stats",
        type=Path,
        default=here / "edge-corpus-stats.tsv",
        help="Output TSV for per-edge overlap metrics.",
    )
    parser.add_argument(
        "--write-graph",
        action="store_true",
        help="Write the enriched GraphML back to the graph path.",
    )
    return parser.parse_args()


def normalize_text(text: object) -> str:
    normalized = unicodedata.normalize("NFKC", str(text)).lower()
    normalized = normalized.replace("&", " and ")
    normalized = re.sub(r"[-_/,:;()\[\]{}]+", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()


def topic_aliases(label: str) -> set[str]:
    base = normalize_text(label)
    aliases = {base}
    tokens = base.split()
    if len(tokens) >= 3 and tokens[-1] in GENERIC_SUFFIXES:
        aliases.add(" ".join(tokens[:-1]))
    return {alias for alias in aliases if alias}


def load_corpus_texts(corpus_path: Path) -> dict[str, str]:
    payload = json.loads(corpus_path.read_text())
    texts: dict[str, str] = {}

    for record in payload["records"]:
        parts = [record.get("folder", ""), Path(record["file"]).stem]
        metadata = record.get("metadata", {}) or {}
        for key in ("/Title", "/Subject", "/Keywords"):
            if metadata.get(key):
                parts.append(metadata[key])
        for key in ("keywords", "title_phrases", "reference_phrases"):
            parts.extend(record.get(key, []) or [])
        parts.append(record.get("front_excerpt", "") or "")
        texts[Path(record["file"]).name] = f" {normalize_text(' '.join(str(part) for part in parts if part))} "

    return texts


def direct_topic_papers(label: str, corpus_texts: dict[str, str]) -> set[str]:
    aliases = topic_aliases(label)
    papers: set[str] = set()
    for filename, text in corpus_texts.items():
        if any(f" {alias} " in text for alias in aliases):
            papers.add(filename)
    return papers


def add_node_counts(graph: nx.DiGraph, corpus_texts: dict[str, str]) -> None:
    total_papers = max(len(corpus_texts), 1)

    for node, data in graph.nodes(data=True):
        direct = direct_topic_papers(str(data.get("label", node)), corpus_texts)
        data["direct_papers"] = direct

    for node in nx.topological_sort(graph):
        aggregated = set(graph.nodes[node]["direct_papers"])
        for child in graph.predecessors(node):
            aggregated |= graph.nodes[child]["paper_set"]
        graph.nodes[node]["paper_set"] = aggregated
        graph.nodes[node]["direct_paper_count"] = len(graph.nodes[node]["direct_papers"])
        graph.nodes[node]["paper_count"] = len(aggregated)
        graph.nodes[node]["paper_fraction"] = round(len(aggregated) / total_papers, 6)


def add_edge_weights(graph: nx.DiGraph) -> None:
    for source, target, data in graph.edges(data=True):
        source_set = graph.nodes[source]["paper_set"]
        target_set = graph.nodes[target]["paper_set"]
        overlap = source_set & target_set
        union = source_set | target_set
        if source_set and target_set:
            cosine = len(overlap) / ((len(source_set) * len(target_set)) ** 0.5)
        else:
            cosine = 0.0
        data["paper_overlap_count"] = len(overlap)
        data["paper_overlap_jaccard"] = round(len(overlap) / len(union), 6) if union else 0.0
        data["paper_overlap_cosine"] = round(cosine, 6)


def write_topic_stats(graph: nx.DiGraph, path: Path) -> None:
    rows = []
    for node, data in graph.nodes(data=True):
        rows.append(
            {
                "index": int(data.get("index", 0)),
                "topic_id": node,
                "label": str(data.get("label", node)),
                "top_domain": str(data.get("top_domain", "")),
                "depth_hint": int(data.get("depth_hint", 0)),
                "direct_paper_count": int(data.get("direct_paper_count", 0)),
                "paper_count": int(data.get("paper_count", 0)),
                "paper_fraction": float(data.get("paper_fraction", 0.0)),
            }
        )

    rows.sort(key=lambda row: row["index"])
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "index",
                "topic_id",
                "label",
                "top_domain",
                "depth_hint",
                "direct_paper_count",
                "paper_count",
                "paper_fraction",
            ],
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerows(rows)


def write_edge_stats(graph: nx.DiGraph, path: Path) -> None:
    rows = []
    for source, target, data in graph.edges(data=True):
        rows.append(
            {
                "source": source,
                "source_label": str(graph.nodes[source].get("label", source)),
                "target": target,
                "target_label": str(graph.nodes[target].get("label", target)),
                "relation": str(data.get("relation", "")),
                "paper_overlap_count": int(data.get("paper_overlap_count", 0)),
                "paper_overlap_jaccard": float(data.get("paper_overlap_jaccard", 0.0)),
                "paper_overlap_cosine": float(data.get("paper_overlap_cosine", 0.0)),
            }
        )

    rows.sort(
        key=lambda row: (
            -row["paper_overlap_count"],
            -row["paper_overlap_jaccard"],
            row["source_label"].lower(),
            row["target_label"].lower(),
        )
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "source",
                "source_label",
                "target",
                "target_label",
                "relation",
                "paper_overlap_count",
                "paper_overlap_jaccard",
                "paper_overlap_cosine",
            ],
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerows(rows)


def clean_ephemeral_attrs(graph: nx.DiGraph) -> None:
    for _, data in graph.nodes(data=True):
        data.pop("direct_papers", None)
        data.pop("paper_set", None)


def main() -> None:
    args = parse_args()
    graph = nx.read_graphml(args.graph)
    corpus_texts = load_corpus_texts(args.corpus_json)

    add_node_counts(graph, corpus_texts)
    add_edge_weights(graph)
    write_topic_stats(graph, args.topic_stats)
    write_edge_stats(graph, args.edge_stats)

    clean_ephemeral_attrs(graph)
    if args.write_graph:
        nx.write_graphml(graph, args.graph, named_key_ids=True)


if __name__ == "__main__":
    main()
