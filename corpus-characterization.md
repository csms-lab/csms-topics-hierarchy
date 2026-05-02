# Corpus Characterization

## Scope

The current topic structure is seeded from a local paper library rooted at `/Users/kreyes/Desktop/Library`.

The local PDF corpus mined for this pass contains `51` papers distributed across the following folders:

- `MCTS : RL`: `13`
- `Active Subpaces for BO`: `7`
- `Level Sets`: `5`
- `Reasoning`: `5`
- `Foundation Models for Materials Science`: `4`
- `Kalman Filters`: `3`
- `Math`: `3`
- `Parallel-in-time`: `3`
- `Robotics`: `3`
- `Math Physics`: `2`
- `Library`: `1`
- `M2DT`: `1`
- `Sequential Decision General`: `1`

These folders give the present structure a clear bias toward sequential decision-making, Monte Carlo tree search, Bayesian optimization, active subspaces, inverse problems, level set methods, mathematical structures, robotics, reasoning, and AI for materials science.

## What Was Mined

The current artifacts were generated from three main sources:

1. Local paper metadata and front matter
   - folder names
   - PDF metadata fields
   - embedded keyword fields when present
   - title phrases and front-matter terminology

2. Local reference sections
   - `591` extracted reference phrases
   - `556` unique extracted reference phrases
   - `57` DOI-like identifiers
   - `190` arXiv-like identifiers

3. Citation-expanded cited works
   - a manually resolved high-signal subset of `14` cited papers
   - cited-paper abstracts, keyword metadata, and bibliographic descriptions used to expand the vocabulary around active subspaces, Bayesian optimization, model reduction, knowledge-gradient methods, and Monte Carlo tree search

## What The Files Represent

- `topics-hierarchy.txt` is the original nested-list view used to seed the structure.
- `topics-flat.tsv` is the flat node inventory. Each row contains a stable topic ID, a zero-based index, a depth hint inherited from the seed hierarchy, a top-domain label, and a provisional terminal flag.
- `topics.graphml` is the polyhierarchical graph representation in a standard exchange format. It contains `238` topic nodes and `255` directed edges in the current pass, along with corpus-derived node and edge metrics.
- `topic-corpus-stats.tsv` summarizes per-topic direct and propagated paper counts.
- `edge-corpus-stats.tsv` summarizes per-edge paper overlap counts and normalized overlap weights.

In the GraphML file:

- `child_of` edges encode the primary hierarchy
- additional curated cross-links encode secondary parent relationships where a topic naturally belongs under more than one parent
- `terminal=true` currently marks nodes with no child topics in the present graph
- `paper_count` counts local papers matched either directly to a topic or to topics nested beneath it in the current graph
- `paper_overlap_count` counts local papers supporting both endpoints of an edge

These corpus weights are approximate phrase-matching metrics, not hand-curated paper annotations. They are derived from folder names, PDF metadata, extracted keywords, title phrases, front excerpts, and mined reference phrases in the current local corpus.

## Coverage And Limitations

This is a local-corpus-first structure, not a finished ontology.

What is covered well in the current pass:

- topics explicitly named in the local PDFs
- repeated phrases and terminology from local reference sections
- high-signal cited works that shape the main branches of the structure

What is not yet complete:

- full-text retrieval and keyword extraction for every cited paper in every reference list
- normalization of all synonyms and near-duplicates
- enforcement of the target rule that terminal topics should usually map to roughly `2` to `3` papers in the test corpus

Accordingly, the current graph should be treated as a working seed graph: useful for clustering and iteration, but still expected to change as more cited works are resolved and topic labels are normalized.
