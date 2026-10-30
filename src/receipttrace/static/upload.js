import { request, APIError } from "./api.js";
import { translate, messages } from "./i18n.js";
import { element as el, fieldNames, valueText } from "./ui.js";
import { checkFile, fieldChanges, readReceipt } from "./upload-client.js";

export function mountUploads(initialLanguage) {
  let language = initialLanguage;
  const t = (key, values) => translate(language, key, values);
  const $ = (selector) => document.querySelector(selector);
  const state = {
    file: null,
    url: null,
    result: null,
    draft: {},
    validation: null,
    validatedDraft: null,
    busy: false,
    capability: null,
    error: null,
    phase: "choose",
    elapsed: 0,
    events: [],
    reason: "",
    exported: false,
  };
  const record = (action) => state.events.push({ action, at_utc: new Date().toISOString() });
  const currentRaw = () => ({
    ...state.result.raw,
    ...Object.fromEntries(fieldNames.map((field) => [field, state.draft[field]?.trim() || null])),
  });
  const currentValidated = () => state.validatedDraft === JSON.stringify(state.draft);

  function render() {
    const enabled = state.capability?.enabled;
    $("#upload-offline").hidden = enabled !== false && state.error !== "capability";
    $("#upload-offline").textContent =
      state.error === "capability" ? t("upload_connection") : t("upload_disabled");
    $("#upload-file").disabled = state.busy || !enabled;
    $("#upload-policy").disabled = state.busy || !enabled || Boolean(state.result);
    $("#upload-consent").disabled = state.busy || !enabled;
    $("#upload-read").disabled =
      !state.file ||
      state.busy ||
      !enabled ||
      !$("#upload-consent").checked ||
      Boolean(state.result);
    $("#upload-reset").disabled = state.busy || !state.file;
    $("#upload-file-name").textContent = state.file ? state.file.name : t("upload_no_file");
    $("#upload-progress").hidden = !state.busy;
    $("#upload-elapsed").textContent = t("upload_wait", { n: state.elapsed });
    $("#upload-message").hidden = !state.error || state.error === "capability";
    if (state.error)
      $("#upload-message").textContent = t(
        messages[language][`upload_error_${state.error}`]
          ? `upload_error_${state.error}`
          : "upload_error_generic",
      );
    for (const node of document.querySelectorAll("[data-upload-step]")) {
      const active = node.dataset.uploadStep === state.phase;
      node.setAttribute("aria-current", active ? "step" : "false");
      node.classList.toggle("active", active);
    }
    $("#upload-preview-empty").hidden = Boolean(state.url);
    $("#upload-preview").hidden = !state.url;
    if (state.url) $("#upload-preview").src = state.url;
    $("#upload-results").hidden = !state.result;
    $("#upload-guide").hidden = Boolean(state.result);
    if (!state.result) return;
    const found = fieldNames.filter((field) => state.result.raw[field] !== null).length;
    $("#upload-found").textContent = t("upload_found", { n: found });
    $("#upload-status").textContent = t(
      state.result.status === "empty" ? "upload_empty" : "upload_needs_review",
    );
    const fields = fieldNames.map((field) => {
      const source = state.result.evidence.fields[field];
      const label = t(field);
      const input = el("input", {
        id: `uploaded-${field}`,
        class: "field-input",
        type: "text",
        maxlength: "64",
        autocomplete: "off",
        "aria-label": t("upload_edit", { field: label }),
      });
      input.value = state.draft[field] ?? "";
      input.disabled = state.busy;
      input.addEventListener("input", () => {
        state.draft[field] = input.value;
        state.exported = false;
        state.phase = "review";
        state.validatedDraft = null;
        updateValidation();
      });
      const evidence = source?.candidates?.map((candidate) => candidate.text).join(" · ");
      return el(
        "div",
        { class: "upload-field" },
        el("label", { for: `uploaded-${field}` }, label),
        el(
          "p",
          { class: "small muted" },
          t("upload_original", { value: valueText(state.result.raw[field], t("upload_missing")) }),
        ),
        input,
        el(
          "p",
          { class: `small ${source?.ambiguous ? "upload-warning" : "muted"}` },
          source?.ambiguous
            ? t("upload_ambiguous")
            : evidence
              ? t("upload_evidence", { text: evidence })
              : t("upload_no_evidence"),
        ),
      );
    });
    $("#upload-fields").replaceChildren(...fields);
    $("#upload-text").textContent = state.result.evidence.rows.join("\n") || t("upload_empty");
    $("#upload-fingerprint").textContent = `SHA-256: ${state.result.source.sha256}`;
    $("#upload-duration").textContent = t("upload_duration", { n: state.result.seconds });
    $("#upload-resized").hidden = !state.result.source.resized;
    $("#upload-reason").value = state.reason;
    $("#upload-reason").disabled = state.busy;
    $("#upload-validate").disabled = state.busy;
    updateValidation();
    $("#upload-events").replaceChildren(
      ...state.events.map((event) =>
        el(
          "li",
          {},
          `${new Date(event.at_utc).toLocaleTimeString(language === "pt" ? "pt-BR" : "en-US")} · ${t(`upload_event_${event.action}`)}`,
        ),
      ),
    );
  }

  function updateValidation() {
    if (!state.result) return;
    for (const node of document.querySelectorAll("[data-upload-step]")) {
      const active = node.dataset.uploadStep === state.phase;
      node.setAttribute("aria-current", active ? "step" : "false");
      node.classList.toggle("active", active);
    }
    const changed = fieldChanges(state.result.raw, state.draft).length;
    $("#upload-edit-note").textContent = t(changed ? "upload_changed" : "upload_unchanged", {
      n: changed,
    });
    const validation = currentValidated() ? state.validation : null;
    const checks = validation?.checks ?? [];
    const pass = checks.filter((check) => check.status === "pass").length;
    const skipped = checks.filter((check) => check.status === "skipped").length;
    const issues = checks.filter((check) => ["invalid", "mismatch"].includes(check.status)).length;
    $("#upload-checks").textContent = validation
      ? t("upload_checks_summary", { pass, skipped, issues })
      : t("upload_check_pending");
    const explanations = [];
    for (const field of fieldNames) {
      const invalid = validation?.normalized?.[field]?.status === "invalid";
      $(`#uploaded-${field}`).setAttribute("aria-invalid", String(Boolean(invalid)));
      if (invalid) explanations.push(t("upload_invalid_field", { field: t(field) }));
    }
    for (const check of checks) {
      if (check.code === "receipt_total" && check.status === "mismatch")
        explanations.push(
          t("upload_total_mismatch", { expected: check.expected, observed: check.observed }),
        );
      if (check.code === "receipt_total" && check.status === "skipped")
        explanations.push(t("upload_total_skipped"));
    }
    $("#upload-check-details").replaceChildren(...explanations.map((text) => el("li", {}, text)));
    $("#upload-download").disabled =
      state.busy || !validation || (changed > 0 && !state.reason.trim());
    $("#upload-reason-note").hidden = !(changed > 0 && !state.reason.trim());
  }

  function clear(resetFile = true) {
    if (state.url) URL.revokeObjectURL(state.url);
    Object.assign(state, {
      file: null,
      url: null,
      result: null,
      draft: {},
      validation: null,
      validatedDraft: null,
      error: null,
      phase: "choose",
      events: [],
      reason: "",
      exported: false,
    });
    if (resetFile) $("#upload-file").value = "";
    $("#upload-consent").checked = false;
    $("#upload-preview").removeAttribute("src");
    render();
  }

  $("#upload-file").addEventListener("change", () => {
    const file = $("#upload-file").files[0];
    clear(false);
    if (!file) return;
    const error = checkFile(file);
    if (error) {
      state.error = error;
      render();
      return;
    }
    state.file = file;
    state.url = URL.createObjectURL(file);
    record("selected");
    render();
  });
  $("#upload-consent").addEventListener("change", render);
  $("#upload-policy").addEventListener("change", () => {
    if (state.result) {
      state.result = null;
      state.phase = "choose";
      state.draft = {};
    }
    render();
  });
  $("#upload-reset").addEventListener("click", () => clear());
  $("#upload-read").addEventListener("click", async () => {
    if (state.busy || !state.file) return;
    state.busy = true;
    state.error = null;
    state.result = null;
    state.phase = "read";
    state.elapsed = 0;
    const started = performance.now();
    record("started");
    render();
    const timer = setInterval(() => {
      state.elapsed = Math.floor((performance.now() - started) / 1000);
      $("#upload-elapsed").textContent = t("upload_wait", { n: state.elapsed });
    }, 1000);
    try {
      const result = await readReceipt(state.file, $("#upload-policy").value);
      state.result = result;
      state.draft = Object.fromEntries(fieldNames.map((field) => [field, result.raw[field] ?? ""]));
      state.validation = result.validation;
      state.validatedDraft = JSON.stringify(state.draft);
      state.phase = "review";
      state.reason = "";
      record("read");
    } catch (error) {
      state.error = error instanceof APIError ? error.code : "generic";
      state.phase = "choose";
      record("failed");
    } finally {
      clearInterval(timer);
      state.busy = false;
      render();
    }
  });
  $("#upload-reason").addEventListener("input", (event) => {
    state.reason = event.target.value;
    updateValidation();
  });
  $("#upload-validate").addEventListener("click", async () => {
    if (state.busy || !state.result) return;
    state.busy = true;
    state.error = null;
    render();
    try {
      state.validation = await request("/api/uploads/validate", {
        raw: currentRaw(),
        policy: state.result.numeric_policy,
      });
      state.validatedDraft = JSON.stringify(state.draft);
      state.phase = "export";
      record("checked");
    } catch (error) {
      state.error = error instanceof APIError ? error.code : "generic";
    } finally {
      state.busy = false;
      render();
    }
  });
  $("#upload-download").addEventListener("click", () => {
    if (!state.result || !currentValidated()) return;
    record("exported");
    state.phase = "export";
    const payload = {
      schema_version: 1,
      original: state.result,
      review: {
        current_raw: currentRaw(),
        validation: state.validation,
        changes: fieldChanges(state.result.raw, state.draft),
        reason: state.reason.trim() || null,
        identity: "anonymous_browser_session",
        status: "not_independently_verified",
        events: state.events,
        exported_at_utc: new Date().toISOString(),
        warning: "Not fiscal validation, payment approval or proof of human identity.",
      },
    };
    const url = URL.createObjectURL(
      new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" }),
    );
    const anchor = el("a", {
      href: url,
      download: `receipttrace-${state.result.document_id}.json`,
    });
    document.body.append(anchor);
    anchor.click();
    anchor.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    state.exported = true;
    render();
    $("#upload-checks").textContent = t("upload_downloaded");
  });
  window.addEventListener("beforeunload", (event) => {
    if (state.result && !state.exported && fieldChanges(state.result.raw, state.draft).length) {
      event.preventDefault();
      event.returnValue = "";
    }
  });
  request("/api/uploads/capabilities")
    .then((capability) => {
      state.capability = capability;
      render();
    })
    .catch(() => {
      state.error = "capability";
      state.capability = { enabled: false };
      render();
    });
  render();
  return {
    setLanguage(value) {
      language = value;
      render();
    },
  };
}
