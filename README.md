# csms-topics-hierarchy

This repository contains a working topic vocabulary and graph for organizing and clustering papers across computational science, applied mathematics, materials science, physics, chemistry, biology, earth science, machine learning, AI, and nearby areas.

The current structure is seeded from a locally mined paper library and expanded with a curated citation pass over structurally important referenced works.

Files:

- `topics-hierarchy.txt`: nested-list seed hierarchy
- `topics-flat.tsv`: flat topic table with stable IDs, zero-based indices, depth hints, top-domain labels, and terminal flags
- `topics.graphml`: GraphML topic graph enriched with corpus-derived node counts and edge overlap weights
- `topic-corpus-stats.tsv`: per-topic direct and propagated paper counts in the current local corpus
- `edge-corpus-stats.tsv`: per-edge paper overlap counts and normalized overlap weights
- `scripts/build_corpus_graph_metrics.py`: derive corpus metrics from the mined local library JSON and write them into the GraphML plus TSV summaries
- `scripts/render_topics_graph.py`: deterministic renderer for the GraphML overview image
- `topics-graph.png`: rendered PNG overview of the topic graph, with node size weighted by paper count and edge intensity weighted by topic co-appearance
- `corpus-characterization.md`: description of the local corpus and the mining process used to generate the current structure

To refresh the corpus metrics from the local mined library JSON:

```bash
python3 scripts/build_corpus_graph_metrics.py --write-graph
```

To regenerate the PNG from the enriched GraphML:

```bash
python3 scripts/render_topics_graph.py
```
