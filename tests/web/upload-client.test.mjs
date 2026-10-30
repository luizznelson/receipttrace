import test from "node:test";
import assert from "node:assert/strict";
import {
  checkFile,
  fieldChanges,
  readReceipt,
  MAX_IMAGE_BYTES,
} from "../../src/receipttrace/static/upload-client.js";

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
