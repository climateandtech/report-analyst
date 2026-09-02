# Chunk retrieval evaluation method

This document specifies the matching and ranking calculations used to compare
report-analyst retrieval with ClimRetrieve. It is intended to be sufficiently
precise for the research paper and reproducible from the exported CSV files.

## Experimental unit

The unit of analysis is one `(report, question, retrieval configuration)`
triple. A retrieval configuration fixes:

- embedding model;
- chunk size and overlap;
- retrieval cutoff `k`;
- any reranking or LLM-scoring setting.

The same report-question pairs are evaluated under every configuration.
Configuration comparisons therefore use paired observations. Ranking metrics
include only pairs with at least one expert-annotated evidence span; unjudged
pairs are counted and reported separately rather than treated as retrieval
failures.

## Ground truth

ClimRetrieve supplies report text spans with relevance grades:

- `0`: not relevant;
- `1`: partially or indirectly relevant;
- `2`: relevant;
- `3`: highly relevant.

The graded values are retained for nDCG. Following the ClimRetrieve base
evaluation, binary ranking metrics treat grades `2` and `3` as relevant. Grade
`1` remains part of graded nDCG and strict source-coverage diagnostics.

## Candidate generation versus acceptance

Embedding similarity retrieves and ranks candidate chunks. It does not decide
whether a candidate matches ground truth.

METEOR, BERTScore, and embedding cosine similarity may be reported as
diagnostic scores. They are not acceptance rules: a semantically similar chunk
can omit required evidence, and a long chunk containing a short gold span can
receive a low text-similarity score.

## Text normalization

Both texts are lowercased and converted to ordered alphanumeric token
sequences. Whitespace and punctuation differences therefore do not affect
matching, while token order and completeness remain observable.

## Single-chunk relationships

For retrieved sequence `R` and ground-truth sequence `G`:

1. `exact`: `R = G`.
2. `retrieved_contains_ground_truth`: `G` occurs as a complete contiguous
   subsequence of `R`. This is a ground-truth hit.
3. `ground_truth_contains_retrieved`: `R` occurs inside `G`, but some
   ground-truth evidence is absent. This is recorded as a relationship but is
   **not** a hit.
4. `partial_overlap`: both sides share tokens but neither fully contains the
   other. This is diagnostic only and is **not** a hit.
5. `no_match`: no accepted relationship.

A fraction of matching tokens is never sufficient for a binary hit.

Matches are restricted to evidence spans with the same report and question as
the retrieved chunk. A chunk may contain several such spans. The exported
match table preserves every chunk--span relation, while ranking treats the
chunk as one item with the maximum relevance grade among its matched spans.
Repeated occurrences and additional spans do not create multiple gains at one
rank. Evidence recall separately counts unique matched spans.

## Split ground truth across retrieved chunks

A ground-truth span may cross a chunk boundary. Split matching is restricted to
retrieved chunks that are adjacent in document order.

For each adjacent pair:

1. order chunks by their source `chunk_order`;
2. find the longest suffix of the first chunk equal to a prefix of the second;
3. remove that duplicated overlap;
4. concatenate the ordered token sequences;
5. require the complete ordered ground-truth sequence to occur in the merged
   sequence.

If the pair succeeds, the completion is associated with the later of the two
retrieval ranks. This is the first rank at which the complete evidence is
available. If several spans complete at the same rank, the ranked chunk still
receives one gain equal to their maximum relevance grade.

The current paper configuration tests windows of at most two adjacent chunks.

## Ranking metrics

### Primary: macro nDCG@10

For rank `i` starting at one and ClimRetrieve grade `rel_i`:

`DCG@k = Σ_{i=1..k} rel_i / log2(i + 1)`

`nDCG@k = DCG@k / IDCG@k`

For each chunking configuration, all corpus chunks are matched before
retrieval evaluation. `IDCG` sorts the resulting chunk-level maximum relevance
grades. Thus, one chunk contributes at most one gain even if it contains
several evidence spans. Query nDCG values are macro-averaged, giving each
judged report-question pair equal weight.

### Secondary metrics

- `Precision@k`: accepted grade-2-or-3 hits in the first `k` ranks divided by
  `k`.
- `Recall@k`: accepted grade-2-or-3 chunks in the first `k` ranks divided by
  all grade-2-or-3 corpus chunks for the query and chunking configuration.
- `F1@k`: harmonic mean of Precision@k and Recall@k.
- `Hit@k`: whether at least one grade-2-or-3 item is complete by rank `k`.
- `Complete-set Hit@k`: whether every grade-2-or-3 chunk is retrieved by rank
  `k`.
- `MRR`: reciprocal rank of the first accepted grade-2-or-3 item.
- `AP`: sum of precision at each accepted relevant rank, divided by the total
  number of grade-2-or-3 corpus chunks.
- `MAP`: macro mean of AP across report-question pairs.

We report `k ∈ {1, 3, 5, 10}` and retain per-query rows.

## Boundary and context diagnostics

Ranking metrics are complemented by:

- strict evidence recall over all annotated ClimRetrieve source spans;
- exact, contained, and split hit counts;
- complete-set hit rate;
- mean ground-truth coverage among accepted hits;
- mean retrieved coverage among accepted hits, which quantifies how much of a
  retrieved chunk belongs to the matched gold span;
- partial-candidate count.

Retrieved coverage is descriptive, not an acceptance threshold. It exposes the
context dilution introduced by larger chunks.

## Uncertainty and comparison

Point estimates are macro means over report-question pairs. The notebook
exports 95% percentile confidence intervals from 2,000 query-level bootstrap
resamples with replacement and fixed seed `42`.

Chunk-size comparisons should additionally report paired per-query
differences. Report counts, means, confidence intervals, and the complete
distribution rather than only significance tests.

## Reproducibility artifacts

The notebook exports:

- strict chunk-level relations and directional coverage;
- per-query ranking metrics;
- configuration-level macro summaries;
- query-bootstrap confidence intervals;
- side-by-side chunk excerpts and ranks;
- ground-truth labels and relevance grades.

`tests/fixtures/ct_reit_chunk_matching.json` contains only real CT REIT report
chunks generated at 200 and 400 tokens plus the corresponding real
ClimRetrieve label, context, page, source type, answer, relevance grade, and
annotation flags. Embedding vectors and credentials are not stored.

## References

- Schimanski et al. (2024), [ClimRetrieve: A Benchmarking Dataset for
  Information Retrieval from Corporate Climate
  Disclosures](https://aclanthology.org/2024.emnlp-main.969/).
- Thakur et al. (2021), [BEIR: A Heterogeneous Benchmark for Zero-shot
  Evaluation of Information Retrieval Models](https://arxiv.org/abs/2104.08663).
- Zhang et al. (2020), [BERTScore: Evaluating Text Generation with
  BERT](https://arxiv.org/abs/1904.09675).
- Banerjee and Lavie (2005), [METEOR: An Automatic Metric for MT Evaluation
  with Improved Correlation with Human
  Judgments](https://www.cs.cmu.edu/~alavie/papers/BanerjeeLavie2005-final.pdf).
