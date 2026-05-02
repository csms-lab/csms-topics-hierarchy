# csms-topics-hierarchy

This repository contains a working topic vocabulary and graph for organizing and clustering papers across computational science, applied mathematics, materials science, physics, chemistry, biology, earth science, machine learning, AI, and nearby areas.

The current structure is seeded from a locally mined paper library and expanded with a curated citation pass over structurally important referenced works.

Files:

- `topics-hierarchy.txt`: nested-list seed hierarchy
- `topics-flat.tsv`: flat topic table with stable IDs, zero-based indices, depth hints, top-domain labels, and terminal flags
- `topics.graphml`: GraphML topic graph with primary hierarchy edges and secondary cross-links for polyhierarchy
- `scripts/render_topics_graph.py`: deterministic renderer for the GraphML overview image
- `topics-graph.png`: rendered PNG overview of the topic graph
- `corpus-characterization.md`: description of the local corpus and the mining process used to generate the current structure

To regenerate the PNG:

```bash
python3 scripts/render_topics_graph.py
```
