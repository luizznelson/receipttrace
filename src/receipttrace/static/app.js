import { mountUploads } from "./upload.js";
import { request, APIError, requiresReload } from "./api.js";
import { applyLanguage, messages, translate } from "./i18n.js";
import {
  element as el,
  fieldNames,
  valueText,
  formatNumber,
  numericLocale,
  changesFor,
} from "./ui.js";

const $ = (selector) => document.querySelector(selector);
let language = "pt";
try {
  if (localStorage.getItem("receipttrace-language") === "en") language = "en";
} catch {
  /* Preferences are optional. */
}
const state = {
  language,
  summary: null,
  examples: [],
  selected: null,
  method: "ocr",
  entries: new Map(),
  sequence: 0,
  loading: false,
  busy: false,
  actor: "",
  hero: null,
};
const uploadWorkspace = mountUploads(language);
const t = (key, values) => translate(state.language, key, values);
const entry = () => state.entries.get(`${state.selected}:${state.method}`);

function ensureEntry() {
  const key = `${state.selected}:${state.method}`;
  if (!state.entries.has(key))
    state.entries.set(key, {
      detail: null,
      review: null,
      draft: {},
      actor: state.actor,
      reason: "",
      acknowledgeUnverified: false,
      acknowledgeFindings: false,
      conflict: false,
      uncertain: false,
      message: null,
    });
  return state.entries.get(key);
}

function setText(selector, text) {
  $(selector).textContent = text;
}
function badge(text, tone = "neutral") {
  return el("span", { class: `badge ${tone}` }, text);
}
function moneyText(value) {
  return valueText(value, t("absent"));
}

function renderSummary() {
  if (!state.summary) return;
  const { methods, total_gain: gain } = state.summary;
  const ai = methods.gemini,
    ocr = methods.ocr;
  setText(
    "#metric-correct",
    t("ratio", { n: ai.metrics.total.correct, d: ai.metrics.total.annotated_documents }),
  );
  setText("#metric-gain", `+${gain}`);
  setText(
    "#metric-time",
    t("seconds", { value: formatNumber(state.language, ai.latency.p50_seconds) }),
  );
  setText(
    "#metric-cost",
    new Intl.NumberFormat(numericLocale(state.language), {
      style: "currency",
      currency: "USD",
    }).format(Number(ai.cost_summary.estimated_known_usage_usd)),
  );
  setText("#mode-badge", t(state.summary.review_enabled ? "local_mode" : "readonly_mode"));
  setText(
    "#answer-quality",
    t("answer_quality", {
      ai: ai.metrics.total.correct,
      n: ai.metrics.total.annotated_documents,
      ocr: ocr.metrics.total.correct,
    }),
  );
  setText(
    "#answer-speed",
    t("answer_speed", {
      ai: formatNumber(state.language, ai.latency.p50_seconds),
      ocr: formatNumber(state.language, ocr.latency.p50_seconds),
    }),
  );
  const rows = fieldNames.map((name) =>
    el(
      "tr",
      {},
      el("td", {}, t(name)),
      ...["ocr", "gemini"].map((method) => {
        const metric = methods[method].metrics[name];
        const cell = el("td");
        if (metric.annotated_documents === 0)
          cell.append(el("span", { class: "small muted" }, t("no_references")));
        else
          cell.append(
            el("span", {}, t("ratio", { n: metric.correct, d: metric.annotated_documents })),
            el("progress", {
              class: method === "gemini" ? "ai-progress" : "",
              value: metric.correct,
              max: metric.annotated_documents,
              "aria-label": `${t(name)} · ${t(method === "ocr" ? "ocr" : "ai")}`,
            }),
          );
        return cell;
      }),
    ),
  );
  $("#comparison-rows").replaceChildren(...rows);
  if (state.hero) setText("#hero-total", moneyText(state.hero.raw.total));
}

function renderCases() {
  $("#case-list").replaceChildren(
    ...state.examples.map((example, index) => {
      const button = el(
        "button",
        {
          class: "case-button",
          type: "button",
          "aria-pressed": String(example.id === state.selected),
        },
        el(
          "span",
          { class: "case-number", "aria-hidden": "true" },
          String(index + 1).padStart(2, "0"),
        ),
        t(example.title_key),
      );
      button.addEventListener("click", () => {
        if (state.selected !== example.id && !state.busy) {
          state.selected = example.id;
          loadSelection();
        }
      });
      return button;
    }),
  );
  for (const button of document.querySelectorAll("[data-method]")) {
    button.setAttribute("aria-pressed", String(button.dataset.method === state.method));
    button.disabled = state.busy;
  }
}

function renderStates(current) {
  const detail = current.detail;
  const checks = current.review?.arithmetic ?? detail.arithmetic;
  const reviewStatus = current.review?.review_status ?? "not_started";
  const arithmeticTone =
    checks.status === "passed" ? "success" : checks.status === "findings" ? "danger" : "warning";
  $("#state-badges").replaceChildren(
    badge(t(`extraction_${detail.extraction_status}`), "neutral"),
    badge(t(`arithmetic_${checks.status}`), arithmeticTone),
    badge(t(`review_${reviewStatus}`), reviewStatus === "completed" ? "success" : "neutral"),
  );
}

function renderFields(current) {
  const showCurrent = Boolean(current.review);
  $("#current-heading").hidden = !showCurrent;
  $("#field-rows").replaceChildren(
    ...fieldNames.map((name) => {
      const evaluation = current.detail.evaluation[name];
      const original = current.detail.raw?.[name] ?? null;
      const reference = evaluation.expected;
      const row = el(
        "tr",
        {},
        el("td", {}, t(name)),
        el(
          "td",
          {},
          el("span", { class: "raw-value" }, moneyText(original)),
          el("span", { class: `outcome ${evaluation.outcome}` }, t(evaluation.outcome)),
        ),
        el(
          "td",
          {},
          el(
            "span",
            { class: reference == null ? "small muted" : "raw-value" },
            reference == null ? t("no_reference") : reference,
          ),
        ),
      );
      if (showCurrent) {
        const input = el("input", {
          class: "field-input",
          type: "text",
          "data-field": name,
          "aria-label": `${t("current_value")} · ${t(name)}`,
          autocomplete: "off",
          maxlength: 64,
        });
        input.value = current.draft[name] ?? "";
        input.disabled =
          state.busy ||
          state.loading ||
          current.conflict ||
          current.review.review_status === "unavailable";
        const before = current.review.current_raw?.[name] ?? "";
        input.classList.toggle("dirty", input.value !== before);
        input.addEventListener("input", () => {
          current.draft[name] = input.value;
          input.classList.toggle("dirty", input.value !== before);
          refreshActions();
        });
        row.append(el("td", {}, input));
      }
      return row;
    }),
  );
}

function renderHistory(current) {
  if (!current.review) return;
  const events = current.review.events;
  const date = new Intl.DateTimeFormat(numericLocale(state.language), {
    dateStyle: "short",
    timeStyle: "short",
  });
  const rows = events.map((event) => {
    const node = el(
      "li",
      {},
      el("h4", {}, t(`event_${event.kind}`)),
      el(
        "p",
        { class: "muted small" },
        `${t("revision", { n: event.revision })} · ${date.format(new Date(event.created_at_utc))} · ${event.actor}`,
      ),
      el("p", {}, event.reason),
    );
    if (event.changes.length)
      node.append(
        el(
          "ul",
          {},
          ...event.changes.map((change) =>
            el(
              "li",
              {},
              `${messages[state.language][change.path.slice(1)] ?? change.path}: ${moneyText(change.before)} → ${moneyText(change.after)}`,
            ),
          ),
        ),
      );
    if (event.acknowledge_unverified)
      node.append(el("p", { class: "muted small" }, t("event_unverified")));
    if (event.acknowledge_findings)
      node.append(el("p", { class: "muted small" }, t("event_findings")));
    return node;
  });
  $("#history-list").replaceChildren(
    ...(rows.length ? rows : [el("li", { class: "muted" }, t("no_events"))]),
  );
  $("#export-review").href = `/api/reviews/${encodeURIComponent(current.review.review_id)}/export`;
}

function renderChecks(current) {
  const validation = current.review?.validation ?? current.detail.validation;
  const checks = validation?.checks ?? [];
  $("#checks-list").replaceChildren(
    ...checks.map((check) => {
      const tone =
        check.status === "pass" ? "success" : check.status === "skipped" ? "warning" : "danger";
      const name = messages[state.language][check.code] ?? check.code;
      const reason = check.reason ? (messages[state.language][check.reason] ?? check.reason) : "";
      return el(
        "li",
        {},
        badge(t(check.status), tone),
        el("span", {}, name),
        reason ? el("span", { class: "small muted" }, reason) : null,
      );
    }),
  );
  const items = (current.review?.current_raw ?? current.detail.raw)?.items ?? [];
  const itemNode = (item) =>
    el(
      "li",
      {},
      `${item.description ?? t("unnamed_item")} · ${moneyText(item.amount)} · ${t("quantity")}: ${moneyText(item.quantity)}`,
      item.children?.length ? el("ul", {}, ...item.children.map(itemNode)) : null,
    );
  $("#items-list").replaceChildren(
    ...(items.length ? items.map(itemNode) : [el("li", { class: "muted" }, t("no_items"))]),
  );
}

function renderSource(current) {
  const source = current.detail.source;
  const labels = {
    image_sha256: "image_hash",
    result_sha256: "result_hash",
    run_manifest_sha256: "manifest_hash",
    evaluation_sha256: "evaluation_hash",
  };
  $("#source-details").replaceChildren(
    ...Object.entries(labels).flatMap(([key, label]) => [
      el("dt", {}, t(label)),
      el("dd", {}, source[key]),
    ]),
  );
  setText("#raw-json", JSON.stringify(current.detail.raw, null, 2));
}

function refreshActions() {
  const current = entry();
  const review = current?.review;
  const loading = state.loading || state.busy;
  $("#start-review").disabled = loading;
  for (const button of document.querySelectorAll("[data-method], .case-button"))
    button.disabled = state.busy;
  if (!review) return;
  const dirty = changesFor(review.current_raw ?? {}, current.draft).length;
  const identity = current.actor.trim() !== "" && current.reason.trim() !== "";
  const blocked = loading || current.conflict || review.review_status === "unavailable";
  const acknowledged =
    (!review.validation?.has_findings || current.acknowledgeFindings) &&
    (!review.validation?.has_skipped_checks || current.acknowledgeUnverified);
  $("#save-correction").disabled = blocked || !identity || dirty === 0;
  $("#complete-review").disabled =
    blocked || !identity || dirty > 0 || !acknowledged || review.review_status === "completed";
  $("#discard-draft").disabled = loading || current.conflict || dirty === 0;
  setText(
    "#draft-status",
    dirty
      ? t("changed_fields", { n: dirty })
      : t(review.review_status === "completed" ? "completed_hint" : "no_changes"),
  );
  for (const input of document.querySelectorAll(
    ".field-input, #review-actor, #review-reason, #ack-unverified, #ack-findings",
  ))
    input.disabled = blocked;
}

function renderReview(current) {
  const enabled = state.summary.review_enabled;
  $("#readonly-note").hidden = enabled;
  $("#review-opening").hidden = !enabled || Boolean(current.review);
  $("#review-container").hidden = !current.review;
  $("#review-message").hidden = !current.message;
  if (current.message) {
    setText("#review-message", t(current.message.key));
    $("#review-message").className = `notice ${current.message.error ? "danger" : "success"}`;
  }
  if (!current.review) return;
  $("#review-actor").value = current.actor;
  $("#review-reason").value = current.reason;
  $("#ack-unverified").checked = current.acknowledgeUnverified;
  $("#ack-findings").checked = current.acknowledgeFindings;
  $("#unverified-row").hidden =
    current.review.review_status === "completed" || !current.review.validation?.has_skipped_checks;
  $("#findings-row").hidden =
    current.review.review_status === "completed" || !current.review.validation?.has_findings;
  $("#conflict-panel").hidden = !current.conflict;
  $("#conflict-panel p").textContent = t(current.uncertain ? "uncertain_text" : "conflict_text");
  setText("#revision-label", t("revision", { n: current.review.revision }));
  renderHistory(current);
}

function renderWorkspace() {
  const current = entry();
  if (!current?.detail) return;
  $("#document-workspace").hidden = false;
  $("#receipt-image").src = current.detail.image_url;
  $("#open-image").href = current.detail.image_url;
  setText("#document-id", current.detail.id);
  setText(
    "#document-time",
    t("seconds", { value: formatNumber(state.language, current.detail.seconds) }),
  );
  renderStates(current);
  renderFields(current);
  renderReview(current);
  renderChecks(current);
  renderSource(current);
  refreshActions();
}

async function loadSelection() {
  ensureEntry();
  const sequence = ++state.sequence;
  const current = entry();
  state.loading = true;
  $("#document-workspace").setAttribute("aria-busy", "true");
  $("#load-error").hidden = true;
  renderCases();
  refreshActions();
  try {
    const detail = await request(
      `/api/examples/${encodeURIComponent(state.selected)}?method=${state.method}`,
    );
    if (sequence !== state.sequence) return;
    current.detail = detail;
    renderWorkspace();
  } catch {
    if (sequence !== state.sequence) return;
    $("#document-workspace").hidden = true;
    $("#load-error").hidden = false;
    setText("#load-error-text", t("load_failed"));
  } finally {
    if (sequence === state.sequence) {
      state.loading = false;
      $("#document-workspace").setAttribute("aria-busy", "false");
      refreshActions();
    }
  }
}

function replaceReview(current, review) {
  current.review = review;
  current.draft = Object.fromEntries(
    fieldNames.map((name) => [name, review.current_raw?.[name] ?? ""]),
  );
  current.acknowledgeUnverified = false;
  current.acknowledgeFindings = false;
  current.conflict = false;
  current.uncertain = false;
  current.reason = "";
}

async function action(operation, success) {
  const current = entry();
  if (state.busy || state.loading || !current?.detail) return;
  state.busy = true;
  current.message = null;
  refreshActions();
  try {
    const review = await operation(current);
    replaceReview(current, review);
    if (success) current.message = { key: success, error: false };
  } catch (error) {
    const code = error instanceof APIError ? error.code : "generic";
    if (requiresReload(error, Boolean(current.review))) {
      current.conflict = true;
      current.uncertain = error.uncertain;
    }
    current.message = {
      key: messages[state.language][`error_${code}`] ? `error_${code}` : "error_generic",
      error: true,
    };
  } finally {
    state.busy = false;
    renderCases();
    renderWorkspace();
  }
}

for (const button of document.querySelectorAll("[data-lang]"))
  button.addEventListener("click", () => {
    state.language = button.dataset.lang;
    try {
      localStorage.setItem("receipttrace-language", state.language);
    } catch {
      /* Continue without persisted preference. */
    }
    applyLanguage(state.language);
    uploadWorkspace.setLanguage(state.language);
    renderSummary();
    renderCases();
    renderWorkspace();
    if (!$("#load-error").hidden) setText("#load-error-text", t("load_failed"));
  });
for (const button of document.querySelectorAll("[data-method]"))
  button.addEventListener("click", () => {
    if (state.method !== button.dataset.method && !state.busy) {
      state.method = button.dataset.method;
      loadSelection();
    }
  });
$("#retry-load").addEventListener("click", () => (state.summary ? loadSelection() : initialize()));
$("#start-review").addEventListener("click", () =>
  action(() => request("/api/reviews", { example_id: state.selected, method: state.method })),
);
$("#review-actor").addEventListener("input", (event) => {
  entry().actor = event.target.value;
  state.actor = event.target.value;
  refreshActions();
});
$("#review-reason").addEventListener("input", (event) => {
  entry().reason = event.target.value;
  refreshActions();
});
$("#ack-unverified").addEventListener("change", (event) => {
  entry().acknowledgeUnverified = event.target.checked;
  refreshActions();
});
$("#ack-findings").addEventListener("change", (event) => {
  entry().acknowledgeFindings = event.target.checked;
  refreshActions();
});
$("#review-form").addEventListener("submit", (event) => {
  event.preventDefault();
  if ($("#save-correction").disabled || !$("#review-form").reportValidity()) return;
  action(
    (current) =>
      request(`/api/reviews/${current.review.review_id}/corrections`, {
        expected_revision: current.review.revision,
        correction: {
          actor: current.actor,
          reason: current.reason,
          changes: changesFor(current.review.current_raw, current.draft),
        },
      }),
    "saved",
  );
});
$("#complete-review").addEventListener("click", () => {
  if ($("#complete-review").disabled || !$("#review-form").reportValidity()) return;
  action(
    (current) =>
      request(`/api/reviews/${current.review.review_id}/completion`, {
        expected_revision: current.review.revision,
        completion: {
          actor: current.actor,
          reason: current.reason,
          acknowledge_unverified: current.acknowledgeUnverified,
          acknowledge_findings: current.acknowledgeFindings,
        },
      }),
    "completed",
  );
});
$("#discard-draft").addEventListener("click", () => {
  const current = entry();
  current.draft = Object.fromEntries(
    fieldNames.map((name) => [name, current.review.current_raw?.[name] ?? ""]),
  );
  renderFields(current);
  refreshActions();
});
$("#reload-review").addEventListener("click", () =>
  action((current) => request(`/api/reviews/${current.review.review_id}`), "reloaded"),
);

async function initialize() {
  applyLanguage(state.language);
  $("#load-error").hidden = true;
  try {
    const [summary, examples, hero] = await Promise.all([
      request("/api/summary"),
      request("/api/examples"),
      request("/api/examples/cord-train-shard0-row0006?method=gemini"),
    ]);
    state.summary = summary;
    state.examples = examples;
    state.hero = hero;
    state.selected ??= examples[0].id;
    renderSummary();
    renderCases();
    await loadSelection();
  } catch {
    $("#document-workspace").hidden = true;
    $("#load-error").hidden = false;
    setText("#load-error-text", t("load_failed"));
  }
}

initialize();
