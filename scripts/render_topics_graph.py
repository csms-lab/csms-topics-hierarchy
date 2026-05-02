#!/usr/bin/env python3

from __future__ import annotations

import argparse
from collections import defaultdict
import os
from pathlib import Path
import tempfile

_CACHE_ROOT = Path(tempfile.gettempdir()) / "csms-topics-hierarchy-mpl"
_CACHE_ROOT.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(_CACHE_ROOT / "mplconfig"))
os.environ.setdefault("XDG_CACHE_HOME", str(_CACHE_ROOT / "xdg-cache"))

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import networkx as nx


DOMAIN_COLORS = {
    "Computational mathematics": "#1d4ed8",
    "Sequential decision making": "#b45309",
    "Machine learning and AI": "#15803d",
    "Physical sciences and continuum systems": "#7c3aed",
    "Robotics and geometry": "#0f766e",
    "Mathematical structures": "#be123c",
}

FALLBACK_COLOR = "#4b5563"


def parse_args() -> argparse.Namespace:
    here = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(
        description="Render the CSMS topic graph overview from GraphML."
    )
    parser.add_argument(
        "--graph",
        type=Path,
        default=here / "topics.graphml",
        help="Input GraphML file.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=here / "topics-graph.png",
        help="Output PNG path.",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=200,
        help="PNG resolution.",
    )
    parser.add_argument(
        "--label-size",
        type=float,
        default=5.4,
        help="Label font size.",
    )
    return parser.parse_args()


def normalize_bool(value: object) -> bool:
    return str(value).strip().lower() == "true"


def node_depth(data: dict[str, object]) -> int:
    try:
        return int(data.get("depth_hint", 0))
    except (TypeError, ValueError):
        return 0


def layered_positions(graph: nx.DiGraph) -> dict[str, tuple[float, float]]:
    layers: dict[int, list[str]] = defaultdict(list)
    for node, data in graph.nodes(data=True):
        layers[node_depth(data)].append(node)

    max_layer_size = max((len(nodes) for nodes in layers.values()), default=1)
    max_depth = max(layers, default=0)
    x_spacing = 7.0
    pos: dict[str, tuple[float, float]] = {}

    for depth in range(max_depth + 1):
        nodes = layers.get(depth, [])
        nodes.sort(
            key=lambda n: (
                graph.nodes[n].get("top_domain", ""),
                -graph.out_degree(n),
                graph.nodes[n].get("label", n).lower(),
            )
        )
        offset = (max_layer_size - len(nodes)) / 2.0
        center = (max_layer_size - 1) / 2.0
        for idx, node in enumerate(nodes):
            y = center - (offset + idx)
            x = depth * x_spacing
            pos[node] = (x, y)

    return pos


def build_legend(graph: nx.DiGraph) -> list[object]:
    domains = sorted({data.get("top_domain", "") for _, data in graph.nodes(data=True)})
    handles: list[object] = []
    for domain in domains:
        color = DOMAIN_COLORS.get(domain, FALLBACK_COLOR)
        handles.append(Patch(facecolor=color, edgecolor="none", label=domain))

    handles.extend(
        [
            Line2D(
                [0],
                [0],
                color="#9ca3af",
                lw=1.0,
                label="Primary child_of edge",
            ),
            Line2D(
                [0],
                [0],
                color="#0f766e",
                lw=1.0,
                linestyle="--",
                label="Secondary cross-link",
            ),
        ]
    )
    return handles


def render(graph_path: Path, output_path: Path, dpi: int, label_size: float) -> None:
    graph = nx.read_graphml(graph_path)
    positions = layered_positions(graph)

    max_depth = max((node_depth(data) for _, data in graph.nodes(data=True)), default=0)
    max_layer_size = max(
        (sum(1 for _, data in graph.nodes(data=True) if node_depth(data) == depth) for depth in range(max_depth + 1)),
        default=1,
    )
    fig_width = max(24.0, (max_depth + 1) * 6.0 + 8.0)
    fig_height = max(18.0, max_layer_size * 0.24)

    fig, ax = plt.subplots(figsize=(fig_width, fig_height), dpi=dpi)
    ax.set_facecolor("white")

    primary_edges = [
        (u, v)
        for u, v, data in graph.edges(data=True)
        if data.get("provenance", "primary") == "primary"
    ]
    secondary_edges = [
        (u, v)
        for u, v, data in graph.edges(data=True)
        if data.get("provenance", "primary") != "primary"
    ]

    nx.draw_networkx_edges(
        graph,
        positions,
        edgelist=primary_edges,
        edge_color="#9ca3af",
        width=0.8,
        alpha=0.32,
        arrows=True,
        arrowstyle="-|>",
        arrowsize=7,
        min_source_margin=2,
        min_target_margin=2,
        connectionstyle="arc3,rad=0.02",
        ax=ax,
    )
    nx.draw_networkx_edges(
        graph,
        positions,
        edgelist=secondary_edges,
        edge_color="#0f766e",
        width=0.9,
        alpha=0.45,
        style="dashed",
        arrows=True,
        arrowstyle="-|>",
        arrowsize=7,
        min_source_margin=2,
        min_target_margin=2,
        connectionstyle="arc3,rad=0.14",
        ax=ax,
    )

    node_colors = []
    node_sizes = []
    for _, data in graph.nodes(data=True):
        node_colors.append(DOMAIN_COLORS.get(data.get("top_domain", ""), FALLBACK_COLOR))
        depth = node_depth(data)
        terminal = normalize_bool(data.get("terminal", False))
        size = 150
        if depth <= 1:
            size = 280
        elif not terminal:
            size = 190
        node_sizes.append(size)

    nx.draw_networkx_nodes(
        graph,
        positions,
        node_color=node_colors,
        node_size=node_sizes,
        alpha=0.92,
        linewidths=0.35,
        edgecolors="#ffffff",
        ax=ax,
    )

    labels = {
        node: str(data.get("label", node))
        for node, data in graph.nodes(data=True)
    }
    nx.draw_networkx_labels(
        graph,
        positions,
        labels=labels,
        font_size=label_size,
        font_family="DejaVu Sans",
        font_color="#111827",
        verticalalignment="center",
        horizontalalignment="left",
        ax=ax,
    )

    ax.set_title(
        "CSMS Topics Graph Overview",
        fontsize=18,
        pad=18,
        weight="bold",
    )
    ax.text(
        0.0,
        1.01,
        (
            f"{graph.number_of_nodes()} topics, {graph.number_of_edges()} directed edges. "
            "Columns are depth hints from the seed hierarchy."
        ),
        transform=ax.transAxes,
        fontsize=10,
        color="#374151",
    )

    legend = ax.legend(
        handles=build_legend(graph),
        loc="upper left",
        bbox_to_anchor=(1.01, 1.0),
        frameon=False,
        fontsize=10,
        title="Domains and edge types",
        title_fontsize=11,
    )
    for text in legend.get_texts():
        text.set_color("#111827")

    ax.set_axis_off()
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def main() -> None:
    args = parse_args()
    render(args.graph, args.output, args.dpi, args.label_size)


if __name__ == "__main__":
    main()
