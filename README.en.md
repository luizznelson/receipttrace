# ReceiptTrace

Turns receipt images into structured data and preserves evidence for checking each result.

[Português brasileiro](README.md)

## Problem and approach

Entering receipt data by hand takes attention: a payment amount can be mistaken for the total, and an unreadable field can go unnoticed. ReceiptTrace explores how automated extraction, validation and review evidence can support this task.

The project compares two approaches on the same documents: local OCR, which recognizes text and applies rules, and Gemini, which interprets the image to extract fields. The goal is to assess quality, processing time and cost before choosing an approach. A reduction in manual work has not yet been measured in a real operation.

## Intended users and business decisions

The proposed use case is an administrative or finance team organizing receipts and checking values before using them in another process. Reviewers need to identify uncertain fields; managers need to assess whether extraction quality justifies its processing time and cost. This is a proposed scenario, not a company deployment.

| Business question | Available answer |
|---|---|
| Does AI recover more correct values than OCR? | It recovered five additional totals in this sample. |
| How long does processing take? | Median of 8.33 s with AI and 1.04 s with OCR, with different timing scopes. |
| What was the API cost for this batch? | Estimated USD 0 under the free configuration used; this is not a complete operating cost. |
| Can human checking be removed? | There is no evidence for that. Items and arithmetic consistency have not been certified. |
| Can a result be traced to its source? | Yes, through saved responses, settings and hashes. Human correction history remains to be implemented. |
| Has a reduction in manual work been established? | No. Data entry, checking and correction need a separate evaluation. |

[Business case, questions and proposed measurements (Portuguese)](docs/business-case.md).

## Results on 20 real receipts

On the CORD v2 development sample, Gemini correctly recovered five totals that OCR had either misread or left unanswered.

| Information | Local OCR: correct | Gemini: correct |
|---|---:|---:|
| Receipt total | 14 of 19 | 19 of 19 |
| Subtotal | 9 of 14 | 14 of 14 |
| Tax | 7 of 11 | 11 of 11 |

Denominators differ because not every receipt has every field annotated for comparison. Both methods processed the same 20 documents.

Gemini completed all 20 extractions without technical failures. Median processing time per receipt was **8.33 seconds**, with a **22.52-second** 95th percentile. Local OCR was faster, with a 1.04-second median. The timing scopes differ and are explained in the report.

Known estimated API cost was **USD 0** under the confirmed Free Tier configuration with billing disabled. This is not an invoice and excludes computing and hosting costs.

**Limits:** this is a small training sample already used during development. It does not establish performance on unseen documents. Item accuracy has not been measured. All 76 arithmetic checks were skipped because required components were missing; correct field extraction therefore does not certify financial consistency.

[Report and reproduction instructions (Portuguese)](docs/reports/gemini-development-20.md) · [Per-document results](docs/reports/gemini-development-20.json) · [Detailed comparison](docs/reports/ocr-vs-gemini-development-20.json)

## What works today

- Public data acquisition and file integrity verification.
- Local OCR and Gemini 3.5 Flash-Lite extraction.
- Schema validation, original text preservation and explicit monetary rules.
- Independent evaluation that includes failures and unanswered fields.
- Saved responses, settings and file hashes for auditing.

The current application runs through a command line. Human review, the application API and the user interface remain to be implemented. The planned workflow is: image → extraction → validation → review → export.

## Check the results without an API

Requirements: Python 3.14 and uv. From the repository root:

```powershell
uv sync --locked
uv run receipttrace prepare-cord
uv run receipttrace verify-sample
uv run receipttrace evaluate-extraction --sample data/processed/cord-inspection --run docs/reports/evidence/gemini-development-20 --output runs/gemini-replay.json
```

Preparation downloads about 490 MB and selects 20 documents using seed 42. If the sample already exists, run only verification and evaluation. Choose a new output file. This evaluation uses saved responses: it requires no API key and sends no images to a provider.

To generate new extractions, follow the [Gemini setup guide (Portuguese)](docs/gemini.md). Credentials belong in the root `.env`, excluded from Git. [Local OCR (Portuguese)](docs/ocr.md) requires no external inference API. Dependency versions are locked in `uv.lock`.

## How to audit the project

Each run records the source image, configuration, prompt, response, processing time and file hashes. The evaluator verifies integrity and compares extracted values with official annotations. Extractors receive only images; expected answers are used separately during evaluation.

Saved results allow metrics to be recalculated without new AI calls. New inference may produce different responses. The [report (Portuguese)](docs/reports/gemini-development-20.md) explains the measurement conditions and descriptive metadata differences when replaying the historical OCR evaluation.

## Product and technical documentation

- [Problem and business questions](docs/business-case.md)
- [Presentation and future interface plan](docs/presentation.md)
- [Scope and acceptance criteria](docs/scope.md)
- [Architecture and responsibilities](docs/architecture.md)
- [Data and evaluation protocol](docs/evaluation.md)
- [Fields, numbers and arithmetic checks](docs/domain.md)
- [Environment and quality checks](docs/development.md)
- [Implementation milestones](docs/roadmap.md)
- [Contribution and writing standards](CONTRIBUTING.md)

The detailed technical guides are currently in Portuguese; this README provides the English project overview.

## Data, attribution and transparency

Receipts come from the [public CORD v2 dataset](https://huggingface.co/datasets/naver-clova-ix/cord-v2), by the [CORD authors](https://github.com/clovaai/cord), under CC BY 4.0. Images and annotations are not bundled in this repository; published evidence contains derived extraction results. Dataset licensing is separate from code licensing.

The project does not yet establish support for Brazilian fiscal documents or invoice–purchase order matching. AI assisted development and documentation. The maintainer remains responsible for understanding, reviewing and verifying the work.
