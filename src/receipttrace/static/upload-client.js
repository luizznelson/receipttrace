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
export async function readReceipt(file, policy, { timeoutMs = 70000 } = {}) {
  const invalid = checkFile(file);
  if (invalid) throw new APIError(invalid, 0);
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(`/api/uploads?policy=${encodeURIComponent(policy)}`, {
      method: "POST",
      headers: { "Content-Type": file.type, Accept: "application/json" },
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
