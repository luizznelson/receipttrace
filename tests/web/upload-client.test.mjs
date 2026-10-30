import test from "node:test";
import assert from "node:assert/strict";
import {
  checkFile,
  fieldChanges,
  readReceipt,
  GEMINI_CONSENT,
  GEMINI_TIMEOUT_MS,
  MAX_IMAGE_BYTES,
  OCR_TIMEOUT_MS,
} from "../../src/receipttrace/static/upload-client.js";
import { messages } from "../../src/receipttrace/static/i18n.js";

test("file checks reject unsupported, empty and excessive uploads before network", () => {
  assert.equal(checkFile({ type: "application/pdf", size: 100 }), "image_required");
  assert.equal(checkFile({ type: "image/png", size: 0 }), "request_too_large");
  assert.equal(checkFile({ type: "image/jpeg", size: MAX_IMAGE_BYTES + 1 }), "request_too_large");
  assert.equal(checkFile({ type: "image/jpeg", size: 100 }), null);
});
test("export changes preserve original writing and explicit missing values", () => {
  assert.deepEqual(
    fieldChanges({ total: "R$ 1.234,56", tax: null }, { total: "1.234,57", tax: "" }),
    [{ field: "total", before: "R$ 1.234,56", after: "1.234,57" }],
  );
  assert.deepEqual(fieldChanges({ total: "10,00" }, { total: "" }), [
    { field: "total", before: "10,00", after: null },
  ]);
});
test("receipt bytes are sent once with the selected numeric convention", async (t) => {
  const file = new File(["synthetic-image"], "test.png", { type: "image/png" });
  let calls = 0;
  t.mock.method(globalThis, "fetch", async (path, options) => {
    calls++;
    assert.equal(path, "/api/uploads?policy=brl-grouped");
    assert.equal(options.body, file);
    assert.equal(options.headers["Content-Type"], "image/png");
    return Response.json({ raw: {}, source: {}, evidence: {}, validation: {} });
  });
  await readReceipt(file, "brl-grouped");
  assert.equal(calls, 1);
});
test("server busy and image errors retain their meaning without retry", async (t) => {
  let calls = 0;
  t.mock.method(globalThis, "fetch", async () => {
    calls++;
    return Response.json({ error: { code: "ocr_busy" } }, { status: 429 });
  });
  await assert.rejects(
    readReceipt(new File(["test"], "test.png", { type: "image/png" }), "brl-grouped"),
    { code: "ocr_busy" },
  );
  assert.equal(calls, 1);
});
test("upload timeout cancels the request without retrying", async (t) => {
  t.mock.method(
    globalThis,
    "fetch",
    (_path, { signal }) =>
      new Promise((_resolve, reject) => {
        signal.addEventListener("abort", () => reject(new DOMException("timeout", "AbortError")));
      }),
  );
  await assert.rejects(
    readReceipt(new File(["test"], "test.png", { type: "image/png" }), "brl-grouped", {
      timeoutMs: 5,
    }),
    { code: "request_timeout" },
  );
});
test("malformed successful response is rejected", async (t) => {
  t.mock.method(globalThis, "fetch", async () => Response.json({ unrelated: true }));
  await assert.rejects(
    readReceipt(new File(["test"], "test.png", { type: "image/png" }), "brl-grouped"),
    { code: "invalid_response" },
  );
});

test("CSV neutralizes spreadsheet formulas and escapes quoted values", async () => {
  const { csvCell } = await import("../../src/receipttrace/static/upload-client.js");
  for (const value of ["=SUM(A1:A2)", "+cmd", "@SUM(1)", "-cmd", "  =1", "\t=1"])
    assert.equal(csvCell(value)[1], String.fromCharCode(39));
  assert.equal(csvCell("1.234,56"), '"1.234,56"');
  assert.equal(csvCell('a"b;c'), '"a""b;c"');
});
test("CSV preserves original and reviewed values, reason and source hash", async () => {
  const { receiptCSV } = await import("../../src/receipttrace/static/upload-client.js");
  const text = receiptCSV(
    { total: "62,000" },
    { total: "61,799" },
    { total: "Total" },
    "=untrusted",
    "image-hash",
  );
  assert.ok(text.startsWith("\uFEFF"));
  assert.ok(text.includes('"62,000";"61,799"'));
  assert.ok(text.includes("'="));
  assert.ok(text.includes("image-hash"));
  assert.equal(text.split("\r\n").length, 6);
});
test("AI reading sends explicit consent per request and waits long enough for the fallback", async (t) => {
  const file = new File(["synthetic-image"], "test.png", { type: "image/png" });
  const seen = [];
  t.mock.method(globalThis, "fetch", async (path, options) => {
    seen.push({ path, headers: options.headers });
    return Response.json({ raw: {}, source: {}, evidence: {}, validation: {} });
  });
  await readReceipt(file, "brl-grouped");
  await readReceipt(file, "usd-grouped", { engine: "gemini" });
  assert.equal(seen[0].path, "/api/uploads?policy=brl-grouped");
  assert.equal(seen[0].headers["X-Provider-Consent"], undefined);
  assert.equal(seen[1].path, "/api/uploads?policy=usd-grouped&engine=gemini");
  assert.equal(seen[1].headers["X-Provider-Consent"], GEMINI_CONSENT);
  assert.ok(GEMINI_TIMEOUT_MS > OCR_TIMEOUT_MS);
});
test("every reason the server can give for skipping the AI has a message in both languages", () => {
  const reasons = [
    "gemini_paused",
    "gemini_daily_limit",
    "gemini_client_limit",
    "gemini_rate_limited",
    "gemini_busy",
    "gemini_timeout",
    "gemini_invalid_response",
    "gemini_error",
    "gemini_unavailable",
  ];
  for (const language of ["pt", "en"])
    for (const reason of [...reasons, "generic"])
      assert.ok(
        messages[language][`upload_fallback_${reason}`],
        `${language}.upload_fallback_${reason}`,
      );
});
