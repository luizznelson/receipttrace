import { APIError } from "./api.js";

export const MAX_IMAGE_BYTES = 8 * 1024 * 1024;
export function checkFile(file) {
  if (!file || !["image/png", "image/jpeg"].includes(file.type)) return "image_required";
  if (!file.size || file.size > MAX_IMAGE_BYTES) return "request_too_large";
  return null;
}
export function fieldChanges(original, current) {
  return ["total", "subtotal", "tax", "service", "discount"].flatMap((field) => {
    const after = current[field]?.trim() || null;
    return after === (original[field] ?? null)
      ? []
      : [{ field, before: original[field] ?? null, after }];
  });
}
export const GEMINI_CONSENT = "google-gemini-free";
// The AI path may spend up to ~50 s on Gemini and then fall back to a local OCR run.
export const OCR_TIMEOUT_MS = 70000;
export const GEMINI_TIMEOUT_MS = 130000;
export async function readReceipt(file, policy, { engine = "ocr", timeoutMs } = {}) {
  const invalid = checkFile(file);
  if (invalid) throw new APIError(invalid, 0);
  const useAI = engine === "gemini";
  const controller = new AbortController();
  const timer = setTimeout(
    () => controller.abort(),
    timeoutMs ?? (useAI ? GEMINI_TIMEOUT_MS : OCR_TIMEOUT_MS),
  );
  const headers = { "Content-Type": file.type, Accept: "application/json" };
  // Consent is sent per request, only for the AI path; the server refuses without it.
  if (useAI) headers["X-Provider-Consent"] = GEMINI_CONSENT;
  try {
    const query = `policy=${encodeURIComponent(policy)}${useAI ? "&engine=gemini" : ""}`;
    const response = await fetch(`/api/uploads?${query}`, {
      method: "POST",
      headers,
      body: file,
      signal: controller.signal,
      credentials: "same-origin",
    });
    if (!response.headers.get("content-type")?.includes("application/json"))
      throw new APIError("invalid_response", response.status);
    let result;
    try {
      result = await response.json();
    } catch (error) {
      if (controller.signal.aborted) throw error;
      throw new APIError("invalid_response", response.status);
    }
    if (!response.ok) throw new APIError(result?.error?.code ?? "ocr_failed", response.status);
    if (!result?.raw || !result?.source || !result?.evidence || !result?.validation)
      throw new APIError("invalid_response", response.status);
    return result;
  } catch (error) {
    if (error instanceof APIError) throw error;
    throw new APIError(controller.signal.aborted ? "request_timeout" : "network_error", 0);
  } finally {
    clearTimeout(timer);
  }
}

// Neutralize spreadsheet formulas in every untrusted cell, including notes.
export function csvCell(value) {
  const text = String(value ?? "");
  const safe = /^[\s\uFEFF]*[=+@-]/u.test(text) || /^[\t\r\n]/u.test(text) ? "'" + text : text;
  return '"' + safe.replaceAll('"', '""') + '"';
}
export function receiptCSV(
  original,
  current,
  labels,
  reason,
  sha256,
  headers = ["field", "original", "reviewed", "reason", "source_sha256"],
) {
  const rows = [
    headers,
    ...["total", "subtotal", "tax", "service", "discount"].map((field) => [
      labels[field],
      original[field],
      current[field],
      reason,
      sha256,
    ]),
  ];
  return "\uFEFF" + rows.map((row) => row.map(csvCell).join(";")).join("\r\n");
}
