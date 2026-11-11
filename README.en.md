# ReceiptTrace

[![Quality](https://github.com/luizznelson/receipttrace/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/luizznelson/receipttrace/actions/workflows/ci.yml)

**Read a receipt, check the values and preserve what changed.**

An applied AI engineering portfolio project developed by Luiz. It connects public data, OCR/Gemini comparison, monetary rules, an API and a Portuguese/English interface.

**▶ [Open the live demo](https://receipttrace.onrender.com)** (free hosting: the first visit can take about a minute to wake up)

[Português](README.md) · [Case study](docs/case-study.md) · [Engineering decisions](docs/architecture.md) · [Documentation](docs/README.md)

## In one minute

| | |
| --- | --- |
| **Problem** | An automatic receipt reading can finish without errors and still return the wrong amount. |
| **What I built** | A FastAPI service and a Portuguese/English interface that read a receipt with AI (Gemini) or local OCR, show the evidence beside the image, record each correction with a reason and check whether the sum of the items matches the total. |
| **Measured result** | Correct total on 14 of 19 receipts with OCR and 19 of 19 with Gemini, across 20 public receipts used during development. Not an independent test. |
| **Core decision** | Treat automatic reading as suspect until checked: compare local OCR and Gemini on the same receipts, parse amounts with Decimal, leave conflicting values empty and log each correction with a reason. The image only goes to AI with consent, and local OCR takes over if AI fails. |
| **Next open decision** | Evaluate on a held-out set: the current sample was used during development and item reading has not been evaluated yet. |
| **Where to start** | [Demo](https://receipttrace.onrender.com) · [Case study](docs/case-study.md) · [Engineering decisions](docs/architecture.md) · [How to verify](docs/quality.md) |

![AI reading of a supermarket receipt, with the item table and the sum compared with the total](docs/media/receipttrace-itens.gif)

*Reading a supermarket tax receipt: the AI reads 23 items and their sum is compared with the printed total. The receipt's access key was blurred. [Watch as video (MP4)](docs/media/receipttrace-itens.mp4).*

## 1. The problem: a completed reading can be wrong

People organizing receipts need to check amounts before entering them elsewhere. One public receipt made this concrete: OCR selected **`62,000`** as the total, while the official reference gives **`61,799`**. Gemini recovered the reference value.

Values preserve the document notation: here, `61,799` means `61799` whole units. No currency conversion is applied. [Inspect the preserved responses](docs/reports/evidence/).

The proposed use case is an administrative team identifying uncertainty, checking the image and recording corrections. Labor savings have not been measured in a real operation.

## 2. The solution: automatic reading with reviewable results

**Image → reading → checking → correction with a reason → export.**

- Start with the guided case without a file or API key. Its saved reading is identified as a study example.
- Upload PNG/JPG when uploads are enabled and choose how it is read: **Gemini AI** (free tier, explicit consent, automatic fallback to local OCR with the reason shown) or **local OCR**.
- With AI reading, also check the items it found: their sum is compared with the total (useful for supermarket receipts, which print only a total). This item reading has not been evaluated yet.
- Check five fields beside the image. Conflicting values stay blank; missing components do not become zero.
- Download a CSV table for spreadsheets or JSON with the full session record.

The browser test is temporary. Persistent SQLite history is available for local review of saved examples. Visitor corrections never change study metrics.

```mermaid
flowchart LR
  A[PNG or JPG image] --> B[Validation and cleanup<br/>in an isolated process]
  B --> C{Chosen method}
  C -->|AI, with consent| D[Gemini, free tier]
  C -->|Local OCR| E[OCR and reading rules]
  D -->|limit, failure or timeout| E
  D --> F[Five fields and evidence]
  E --> F
  F --> G[Human check<br/>correction with a reason]
  G --> H[Export CSV or JSON]
```

![Guided example: reading, reference and review](docs/images/receipttrace-overview.jpg)

## 3. What was measured

OCR and Gemini processed the same **20 public CORD v2 receipts**, selected with seed 42. This supports further investigation, not claims about unseen documents.

| Question | Available evidence |
| --- | --- |
| Did AI recover more correct totals? | OCR: **14 of 19**; Gemini: **19 of 19**. Five additional totals recovered. |
| Other fields? | Subtotal: 9/14 → 14/14. Tax: 7/11 → 11/11. Denominators depend on valid references. |
| Processing time? | Median: 1.04 s for OCR and 8.33 s for Gemini, with different timing scopes. |
| API cost? | Estimated US$ 0 under the confirmed Free Tier for that batch; excludes computing and hosting. |
| Were calculations certified? | No. All 76 arithmetic checks lacked required components. |

This training sample was already used during development; no held-out test was run. Item accuracy is unmeasured. Fiscal validation, payment approval and productivity gains are not established.

[Report and limitations](docs/reports/gemini-development-20.md) · [Field comparison](docs/reports/ocr-vs-gemini-development-20.json) · [Evaluation protocol](docs/evaluation.md)

## 4. Architecture decisions and trade-offs

These choices are recorded in the ADRs in [docs/architecture.md](docs/architecture.md) and [docs/architecture-web.md](docs/architecture-web.md).

| Decision | Why | Accepted cost | Evidence |
| --- | --- | --- | --- |
| **Measure OCR and Gemini on the same receipts before choosing** | Pick the extractor from data, not preference: correct total on 14/19 with OCR and 19/19 with Gemini | Gemini is slower (median 8.33 s vs 1.04 s, with different measurement scopes) and quota-bound, so OCR stays as the alternative | [Report](docs/reports/gemini-development-20.md) |
| **Separate extraction from evaluation** | Extractors only receive images; expected answers never enter the prompt | One more step in the flow | [Evaluation](docs/evaluation.md) |
| **Validate contract, rules and accuracy as three separate checks** | Output in the right format can still carry the wrong value | More verification code | [Domain rules](docs/domain.md) |
| **Preserve text and use Decimal** | Interpret separators explicitly and avoid floating-point rounding | Conflicting values stay empty instead of being guessed | [Domain rules](docs/domain.md) |
| **AI only with consent, quotas and OCR fallback** | The image leaves the server only by choice; an AI failure does not take the service down | When it falls back to OCR, total accuracy is lower | [Temporary uploads](docs/uploads.md) (Portuguese), [deployment](docs/deploy.md) |
| **Transactions and expected revisions in review** | Preserve the original and prevent silent overwrites | Persistent review only in local SQLite | [Local review](docs/review.md) |
| **OCR in a separate process** | Bound duration and concurrency without saving uploads | One image at a time per process; not an operating-system security boundary | [Temporary uploads](docs/uploads.md) |
| **Small application: API and UI on one origin, no queues or microservices** | Splitting into services would add operations before proven demand | Scales as a single app; queues only when a need is shown | [ADR-001](docs/architecture.md), [ADR-002](docs/architecture-web.md) |

## 5. Try it locally

Requirements: Python 3.14 and uv. From the project directory:

```powershell
uv sync --locked --extra web --extra ocr
uv run --no-sync receipttrace serve --uploads
```

To try AI reading on your computer, also install the `gemini` extra and set the variables described in [Temporary uploads](docs/uploads.md) (Portuguese); without them only local OCR appears. Open [the local demonstration](http://127.0.0.1:8000). The ready example requires no new inference. Personal-image testing offers Gemini (only if the host configures a key) or local OCR; without a key only OCR appears. See [Deployment](docs/deploy.md). [Interface guide](docs/web.md).

For the ready example alone, install the `web` extra and start `receipttrace serve --read-only`. Stateless field checks and downloads remain available without exposing local review storage. The demo is published at [https://receipttrace.onrender.com](https://receipttrace.onrender.com); the deployment record is in [Deployment](docs/deploy.md).

## 6. Explore the repository

| Directory | Contents |
| --- | --- |
| `src/receipttrace/` | Domain rules, extractors, evaluation, review and API. |
| `src/receipttrace/static/` | Bilingual interface and HTTP clients. |
| `src/receipttrace/webdata/` | Verified public resources required by the installed demonstration. |
| `tests/` | Domain, contract, failure and input-boundary tests. |
| `docs/reports/` | Published results, data provenance and reproducible evidence. |
| `examples/` | Sample configurations and requests without credentials. |

Start with the [documentation index](docs/README.md). Dependency versions are locked in `uv.lock`; see the [development guide](docs/development.md) for local and CI checks. Detailed technical guides are currently in Portuguese.

Data comes from [CORD v2](https://huggingface.co/datasets/naver-clova-ix/cord-v2), by the [CORD authors](https://github.com/clovaai/cord), under CC BY 4.0. Attribution accompanies the three distributed images; data licensing is separate from code licensing. Credentials, the complete dataset and local databases stay outside Git.

AI assisted development. The maintainer remains responsible for understanding, reviewing and verifying the result. See [security limitations](docs/security.md).
