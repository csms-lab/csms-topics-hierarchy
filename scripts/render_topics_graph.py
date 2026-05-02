#!/usr/bin/env python3

from __future__ import annotations

import argparse
from collections import defaultdict
import math
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


def node_depth(data: dict[str, object]) -> int:
    try:
        return int(data.get("depth_hint", 0))
    except (TypeError, ValueError):
        return 0


def node_paper_count(data: dict[str, object]) -> int:
    try:
        return int(data.get("paper_count", 0))
    except (TypeError, ValueError):
        return 0


def edge_overlap_count(data: dict[str, object]) -> int:
    try:
        return int(data.get("paper_overlap_count", 0))
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
                -node_paper_count(graph.nodes[n]),
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


def node_size(paper_count: int) -> float:
    return 75.0 + 60.0 * math.sqrt(max(paper_count, 0))


def draw_weighted_edges(
    graph: nx.DiGraph,
    positions: dict[str, tuple[float, float]],
    ax: plt.Axes,
) -> int:
    weighted_edges = []
    for source, target, data in graph.edges(data=True):
        overlap = edge_overlap_count(data)
        if overlap > 0:
            weighted_edges.append((source, target, overlap))

    max_overlap = max((overlap for _, _, overlap in weighted_edges), default=1)
    weighted_edges.sort(key=lambda item: item[2])

    for source, target, overlap in weighted_edges:
        x1, y1 = positions[source]
        x2, y2 = positions[target]
        strength = math.sqrt(overlap / max_overlap)
        linewidth = 0.25 + 3.0 * strength
        alpha = 0.04 + 0.52 * strength
        ax.plot(
            [x1, x2],
            [y1, y2],
            color="#64748b",
            linewidth=linewidth,
            alpha=alpha,
            solid_capstyle="round",
            zorder=1,
        )

    return len(weighted_edges)


def build_legend(graph: nx.DiGraph) -> list[object]:
    domains = sorted({data.get("top_domain", "") for _, data in graph.nodes(data=True)})
    handles: list[object] = []
    for domain in domains:
        color = DOMAIN_COLORS.get(domain, FALLBACK_COLOR)
        handles.append(Patch(facecolor=color, edgecolor="none", label=domain))

    handles.append(
        Line2D(
            [0],
            [0],
            color="#64748b",
            lw=2.0,
            alpha=0.6,
            label="Edge thickness and opacity ~ paper co-appearance",
        )
    )

    for sample in (1, 5, 15, 30):
        handles.append(
            Line2D(
                [0],
                [0],
                marker="o",
                color="w",
                markerfacecolor="#94a3b8",
                markeredgecolor="#ffffff",
                markersize=math.sqrt(node_size(sample)) / 1.3,
                label=f"Node size ~ {sample} papers",
            )
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
    nonzero_edges = draw_weighted_edges(graph, positions, ax)

    node_colors = []
    node_sizes = []
    for _, data in graph.nodes(data=True):
        node_colors.append(DOMAIN_COLORS.get(data.get("top_domain", ""), FALLBACK_COLOR))
        node_sizes.append(node_size(node_paper_count(data)))

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
            f"{graph.number_of_nodes()} topics, {nonzero_edges} weighted edges with corpus support. "
            "Columns are depth hints from the seed hierarchy. Node area tracks paper count."
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
        title="Domains and corpus weighting",
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
