# ReceiptTrace

Receipt extraction with traceable evaluation and human review.

[Português brasileiro](README.pt-BR.md)

## Status
Specification stage. No extractor, benchmark, API, or interface is implemented yet. No performance results are claimed.

## Purpose
Turn receipt images into structured records, validate supported arithmetic relationships, and preserve evidence for human review. Initial evaluation targets the public CORD v2 benchmark, not Brazilian fiscal compliance or invoice–purchase order matching.

## Planned workflow
Image → extraction → schema validation → arithmetic checks → human review → export.

## Documentation
- [Scope and acceptance criteria](docs/scope.md)
- [Architecture decision](docs/architecture.md)
- [Data provenance and evaluation protocol](docs/evaluation.md)
- [Engineering and contribution rules](CONTRIBUTING.md)
- [Milestones and commits](docs/roadmap.md)

## Reproducibility
Runtime, dependencies and executable commands will be documented and locked when the first data pipeline is implemented. The foundation currently requires only a Markdown reader.

## Data sources
- https://github.com/clovaai/cord
- https://huggingface.co/datasets/naver-clova-ix/cord-v2

CORD is attributed to its original authors and published under CC BY 4.0. Dataset licensing is separate from this project's code licensing. No dataset files are bundled here.

## Engineering transparency
AI assistance must be disclosed in the case study. Maintainers remain responsible for reviewing, testing and understanding every contribution. Implementation and benchmark claims require linked evidence.
