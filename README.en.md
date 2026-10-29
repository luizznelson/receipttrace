# ReceiptTrace

**API key setup:** edit the root `.env`, set `GEMINI_API_KEY`, and save. It is read automatically and excluded from Git. [Gemini guide (Portuguese)](docs/gemini.md).


Receipt extraction with traceable evaluation and human review.

[Português brasileiro](README.md)

## Status
Data acquisition, domain validation, local OCR and Gemini extraction are implemented and evaluated on 20 real CORD v2 receipts. Per-document results and execution evidence are published. The application API, human review and UI remain pending.

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
Runtime and dependencies are locked in uv.lock. Acquisition and verification commands are documented below.

## Data sources
- https://github.com/clovaai/cord
- https://huggingface.co/datasets/naver-clova-ix/cord-v2

CORD is attributed to its original authors and published under CC BY 4.0. Dataset licensing is separate from this project's code licensing. No dataset files are bundled here.

## Engineering transparency
AI assistance must be disclosed in the case study. Maintainers remain responsible for reviewing, testing and understanding every contribution. Implementation and benchmark claims require linked evidence.

## Development and data

Python 3.14 and uv. Install the locked environment with `uv sync --locked`.

```powershell
uv run receipttrace prepare-cord
uv run receipttrace verify-sample
```

Acquisition downloads approximately 490 MB. Initial inspection only uses the first training shard; validation and test remain reserved. [Development instructions (Portuguese)](docs/development.md).

Implemented: revision-pinned and checksum-verified acquisition, deterministic sampling, provenance manifests, offline verification and integrity tests. OCR and Gemini have been evaluated on the same development sample; application API and UI remain pending.

[Initial data inspection report (Portuguese)](docs/reports/cord-inspection.md).

## Schema and validation

Strict input contracts, original text preservation and Decimal arithmetic checks are implemented. [Policies and limitations (Portuguese)](docs/domain.md).

```powershell
uv run receipttrace validate-receipt examples/synthetic-receipt.json --policy idr-grouped
```

This command validates structured data. Images are extracted using the OCR or Gemini commands documented below.

## OCR extraction and initial measurement

Local CPU OCR and independent evaluation are implemented. [Execution and limitations (Portuguese)](docs/ocr.md). On the development sample, total amount was correct in 14 of 19 annotated documents. This is not a held-out result or an all-fields accuracy score. [Full report (Portuguese)](docs/reports/ocr-baseline.md).

## LLM integration

Vision extraction with structured output, offline planning, budget reservation and OCR comparison are implemented. [Configuration and limitations (Portuguese)](docs/llm.md). Gemini Flash-Lite has been evaluated on all 20 development documents. [Report and reproduction (Portuguese)](docs/reports/gemini-development-20.md).

## Free-tier vision API

The recommended path is now Gemini 3.5 Flash-Lite with a dedicated Free Tier project **without billing enabled**. [Setup and execution (Portuguese)](docs/gemini.md). The example selects Gemini with zero rates; confirm the account tier and configure GEMINI_API_KEY locally. No paid-provider fallback. The 20-receipt development evaluation is complete; its results are shown below.

## Real-data results

The same 20 public receipts were used for local OCR and Gemini 3.5 Flash-Lite. Counts are exact matches over valid annotated references.

| Field | Local OCR | Gemini |
|---|---:|---:|
| total | 14/19 | 19/19 |
| subtotal | 9/14 | 14/14 |
| tax | 7/11 | 11/11 |

Gemini: 20/20 technically completed extractions; this does not certify all fields as correct. Latency p50 8.33 s and p95 22.52 s include remote token pre-counting and inference, excluding inter-document pauses. Known estimated API cost: USD 0 under the confirmed Free Tier configuration without billing enabled; this is not an invoice.

This is a small training sample, not a held-out benchmark, and item accuracy is not measured. Service has only one annotated reference; discount has none. [Report, errors, limitations and reproduction (Portuguese)](docs/reports/gemini-development-20.md) · [Per-document results](docs/reports/gemini-development-20.json) · [OCR/Gemini comparison](docs/reports/ocr-vs-gemini-development-20.json). Saved evidence allows offline metric reproduction without API calls.
