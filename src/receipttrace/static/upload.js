import { request, APIError } from "./api.js";
import { translate, messages } from "./i18n.js";
import { element as el, fieldNames, valueText } from "./ui.js";
import { checkFile, fieldChanges, itemChanges, readReceipt, receiptCSV } from "./upload-client.js";

export function mountUploads(initialLanguage) {
  let language = initialLanguage;
  const t = (key, values) => translate(language, key, values);
  const $ = (selector) => document.querySelector(selector);
  const state = {
    file: null,
    url: null,
    result: null,
    draft: {},
    itemDraft: [],
    itemsCheck: null,
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
    sample: false,
    engine: "ocr",
    engineChosen: false,
  };
  const record = (action) => state.events.push({ action, at_utc: new Date().toISOString() });
  const currentRaw = () => ({
    ...state.result.raw,
    items: [],
    items_complete: false,
    currency: null,
    ...Object.fromEntries(fieldNames.map((field) => [field, state.draft[field]?.trim() || null])),
  });
  // Fields and item amounts are validated together: changing either invalidates the last check.
  const draftKey = () => JSON.stringify([state.draft, state.itemDraft]);
  const currentValidated = () => state.validatedDraft === draftKey();
  const originalItems = () => state.result?.items ?? [];
  const currentItems = () =>
    originalItems().map((item, index) => ({
      description: item.description ?? null,
      quantity: item.quantity ?? null,
      unit_price: item.unit_price ?? null,
      amount: state.itemDraft[index]?.trim() || null,
    }));
  const totalChanges = () =>
    fieldChanges(state.result.raw, state.draft).length +
    itemChanges(originalItems(), state.itemDraft).length;
  const shown = (value) => (language === "pt" ? String(value).replace(".", ",") : String(value));
  // The AI path is used only when the server offers it and the visitor chose it.
  const activeEngine = () =>
    state.capability?.engines?.gemini?.available && state.engine === "gemini" ? "gemini" : "ocr";

  function render() {
    const enabled = state.capability?.enabled;
    const engines = state.capability?.engines;
    const aiOffered = Boolean(engines?.gemini?.available);
    $("#upload-engine-group").hidden = !aiOffered;
    $("#upload-engine-group").disabled = state.busy || Boolean(state.result);
    $("#upload-engine-ocr").disabled = engines?.ocr?.available === false;
    $("#upload-engine-gemini").checked = activeEngine() === "gemini";
    $("#upload-engine-ocr").checked = activeEngine() !== "gemini";
    const useAI = activeEngine() === "gemini";
    $("#upload-consent-text").textContent = t(useAI ? "upload_consent_gemini" : "upload_consent");
    $("#upload-privacy").textContent = t(useAI ? "upload_privacy_gemini" : "upload_privacy");
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
    $("#upload-reset").disabled = state.busy || (!state.file && !state.result);
    $("#upload-sample").disabled = state.busy;
    $("#guided-sample").disabled = state.busy;
    $("#upload-retry").hidden = Boolean(enabled);
    $("#upload-sample-note").hidden = !state.sample;
    $("#upload-file-name").textContent = state.sample
      ? t("upload_sample")
      : state.file
        ? state.file.name
        : t("upload_no_file");
    $("#upload-progress").hidden = !state.busy || state.phase !== "read";
    $("#upload-elapsed").textContent = t(useAI ? "upload_wait_gemini" : "upload_wait", {
      n: state.elapsed,
    });
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
    document.querySelector(".upload-image-panel h3").textContent = t(
      state.sample ? "original_image" : "upload_your_image",
    );
    const found = fieldNames.filter((field) => state.result.raw[field] !== null).length;
    $("#upload-found").textContent = t("upload_found", { n: found });
    $("#upload-status").textContent = t(
      state.result.status === "empty" ? "upload_empty" : "upload_needs_review",
    );
    const byAI = state.result.method === "gemini_vision";
    const fallback = state.result.fallback;
    $("#upload-fallback").hidden = !fallback;
    if (fallback)
      $("#upload-fallback").textContent = t(
        messages[language][`upload_fallback_${fallback.reason}`]
          ? `upload_fallback_${fallback.reason}`
          : "upload_fallback_generic",
      );
    $("#upload-text-title").textContent = t(
      byAI ? "upload_text_title_gemini" : "upload_text_title",
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
              : state.sample && state.result.raw[field]
                ? t("upload_saved_field")
                : byAI && state.result.raw[field]
                  ? t("upload_gemini_field")
                  : t("upload_no_evidence"),
        ),
      );
    });
    $("#upload-fields").replaceChildren(...fields);
    renderItems(byAI);
    const limit = $("#upload-check-limit");
    limit.dataset.i18n = byAI ? "upload_check_limit_gemini" : "upload_check_limit";
    limit.textContent = t(limit.dataset.i18n);
    $("#upload-text").textContent = state.sample
      ? t("upload_saved_text")
      : byAI
        ? t("upload_text_gemini")
        : state.result.evidence.rows.join("\n") || t("upload_empty");
    $("#upload-fingerprint").textContent = `SHA-256: ${state.result.source.sha256}`;
    $("#upload-duration").textContent = state.sample
      ? t("upload_sample_duration")
      : byAI
        ? t("upload_duration_gemini", { n: state.result.seconds })
        : t(fallback ? "upload_duration_fallback" : "upload_duration", {
            n: state.result.seconds,
          });
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

  function renderItems(byAI) {
    const items = originalItems();
    $("#upload-items").hidden = !byAI;
    if (!byAI) return;
    $("#upload-items-note").textContent = t(
      items.length ? "upload_items_note" : "upload_items_none",
      {
        n: items.length,
      },
    );
    $("#upload-items-body").replaceChildren(
      ...items.map((item, index) => {
        const input = el("input", {
          id: `uploaded-item-${index}`,
          class: "field-input",
          type: "text",
          maxlength: "64",
          autocomplete: "off",
          "aria-label": t("upload_items_edit", { n: index + 1 }),
        });
        input.value = state.itemDraft[index] ?? "";
        input.disabled = state.busy;
        input.addEventListener("input", () => {
          state.itemDraft[index] = input.value;
          state.exported = false;
          state.phase = "review";
          state.validatedDraft = null;
          updateValidation();
        });
        const text = (value) => value ?? "—";
        return el(
          "tr",
          {},
          el("td", {}, String(index + 1)),
          el("td", {}, text(item.description)),
          el("td", {}, text(item.quantity)),
          el("td", {}, text(item.unit_price)),
          el("td", {}, input),
        );
      }),
    );
  }

  function itemsSummary(check) {
    const target = (state.draft.subtotal ?? "").trim() ? "subtotal" : "total";
    if (!check) return t("upload_items_pending", { target: t(`upload_items_target_${target}`) });
    if (check.status === "unavailable") {
      const key = `upload_items_unavailable_${check.reason}`;
      return t(messages[language][key] ? key : "upload_items_unavailable_generic", {
        list: (check.unreadable_items ?? []).map((index) => index + 1).join(", "),
      });
    }
    return t(check.status === "match" ? "upload_items_match" : "upload_items_mismatch", {
      n: check.items,
      sum: shown(check.sum),
      expected: shown(check.expected),
      target: t(`upload_items_target_${check.target}`),
      difference: shown(String(check.difference).replace("-", "")),
    });
  }

  function updateValidation() {
    if (!state.result) return;
    for (const node of document.querySelectorAll("[data-upload-step]")) {
      const active = node.dataset.uploadStep === state.phase;
      node.setAttribute("aria-current", active ? "step" : "false");
      node.classList.toggle("active", active);
    }
    const changed = totalChanges();
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
    if (!$("#upload-items").hidden) {
      const itemsCheck = currentValidated() ? state.itemsCheck : null;
      $("#upload-items-sum").textContent = itemsSummary(itemsCheck);
      $("#upload-items-sum").classList.toggle("upload-warning", itemsCheck?.status === "mismatch");
      originalItems().forEach((_, index) =>
        $(`#uploaded-item-${index}`)?.setAttribute(
          "aria-invalid",
          String(Boolean(itemsCheck?.unreadable_items?.includes(index))),
        ),
      );
    }
    $("#upload-download").disabled =
      state.busy || !validation || (changed > 0 && !state.reason.trim());
    $("#upload-csv").disabled = $("#upload-download").disabled;
    $("#upload-reason-note").hidden = !(changed > 0 && !state.reason.trim());
  }

  function clear(resetFile = true) {
    if (state.url) URL.revokeObjectURL(state.url);
    Object.assign(state, {
      file: null,
      url: null,
      result: null,
      draft: {},
      itemDraft: [],
      itemsCheck: null,
      validation: null,
      validatedDraft: null,
      error: null,
      phase: "choose",
      events: [],
      reason: "",
      exported: false,
      sample: false,
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
  for (const input of document.querySelectorAll('input[name="upload-engine"]'))
    input.addEventListener("change", () => {
      state.engine = input.value;
      state.engineChosen = true;
      $("#upload-consent").checked = false;
      render();
    });
  $("#upload-policy").addEventListener("change", () => {
    if (state.result) {
      state.result = null;
      state.phase = "choose";
      state.draft = {};
      state.itemDraft = [];
      state.itemsCheck = null;
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
      $("#upload-elapsed").textContent = t(
        activeEngine() === "gemini" ? "upload_wait_gemini" : "upload_wait",
        { n: state.elapsed },
      );
    }, 1000);
    try {
      const result = await readReceipt(state.file, $("#upload-policy").value, {
        engine: activeEngine(),
      });
      state.result = result;
      state.draft = Object.fromEntries(fieldNames.map((field) => [field, result.raw[field] ?? ""]));
      state.itemDraft = (result.items ?? []).map((item) => item.amount ?? "");
      state.itemsCheck = result.items_check ?? null;
      state.validation = result.validation;
      state.validatedDraft = draftKey();
      state.phase = "review";
      state.reason = "";
      record("read");
      if (result.fallback) record("fallback");
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
      const validation = await request("/api/uploads/validate", {
        raw: currentRaw(),
        items: currentItems(),
        policy: state.result.numeric_policy,
      });
      state.validation = validation;
      state.itemsCheck = validation.items_check ?? null;
      state.validatedDraft = draftKey();
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
        current_items: currentItems(),
        item_changes: itemChanges(originalItems(), state.itemDraft),
        items_check: state.itemsCheck,
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
    if (state.result && !state.exported && totalChanges()) {
      event.preventDefault();
      event.returnValue = "";
    }
  });
  function checkAvailability() {
    return request("/api/uploads/capabilities")
      .then((capability) => {
        state.capability = capability;
        if (!state.engineChosen) state.engine = capability.default_engine ?? "ocr";
        if (state.error === "capability") state.error = null;
        render();
      })
      .catch(() => {
        state.error = "capability";
        state.capability = { enabled: false };
        render();
      });
  }
  $("#upload-retry").addEventListener("click", () => {
    state.error = null;
    checkAvailability();
  });
  async function sample() {
    if (state.busy) return;
    clear();
    state.busy = true;
    render();
    try {
      const detail = await request("/api/examples/cord-train-shard0-row0006?method=ocr");
      state.sample = true;
      $("#upload-policy").value = detail.validation.numeric_policy;
      state.url = detail.image_url;
      state.result = {
        ...detail,
        document_id: detail.id,
        method: "saved_ocr_example",
        source: { ...detail.source, sha256: detail.source.image_sha256 },
        numeric_policy: detail.validation.numeric_policy,
        evidence: { rows: [], fields: {} },
        status: "read",
        benchmark_included: false,
        provenance: "saved_public_study_example",
      };
      state.draft = Object.fromEntries(fieldNames.map((field) => [field, detail.raw[field] ?? ""]));
      state.itemDraft = [];
      state.itemsCheck = null;
      state.validation = detail.validation;
      state.validatedDraft = draftKey();
      state.phase = "review";
      record("sample");
      document.getElementById("try").scrollIntoView({ block: "start" });
    } catch (error) {
      state.error = error instanceof APIError ? error.code : "generic";
    } finally {
      state.busy = false;
      render();
    }
  }
  $("#upload-sample").addEventListener("click", sample);
  $("#guided-sample").addEventListener("click", sample);
  $("#upload-csv").addEventListener("click", () => {
    if (!currentValidated() || $("#upload-download").disabled) return;
    const labels = Object.fromEntries(fieldNames.map((field) => [field, t(field)]));
    const csv = receiptCSV(
      state.result.raw,
      currentRaw(),
      labels,
      state.reason,
      state.result.source.sha256,
      ["csv_field", "csv_original", "csv_reviewed", "csv_reason", "csv_source"].map((key) =>
        t(key),
      ),
      originalItems().map((item, index) => [
        `${t("csv_item", { n: index + 1 })} · ${item.description ?? "—"}`,
        item.amount,
        state.itemDraft[index]?.trim() || null,
      ]),
    );
    const url = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" }));
    const anchor = el("a", { href: url, download: `receipttrace-${state.result.document_id}.csv` });
    document.body.append(anchor);
    anchor.click();
    anchor.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    record("exported");
    state.exported = true;
    state.phase = "export";
    render();
  });
  checkAvailability();
  render();
  return {
    setLanguage(value) {
      language = value;
      render();
    },
  };
}
