import test from "node:test";
import assert from "node:assert/strict";
import { request, APIError, requiresReload } from "../../src/receipttrace/static/api.js";

function json(payload, status = 200) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

test("GET and POST preserve the JSON contract and do not retry", async (t) => {
  const calls = [];
  t.mock.method(globalThis, "fetch", async (path, options) => {
    calls.push({ path, options });
    return json({ ok: true });
  });
  assert.deepEqual(await request("/api/health"), { ok: true });
  await request("/api/reviews", { actor: "test" });
  assert.equal(calls.length, 2);
  assert.equal(calls[0].options.method, "GET");
  assert.equal(calls[1].options.method, "POST");
  assert.equal(calls[1].options.body, JSON.stringify({ actor: "test" }));
  assert.equal(calls[1].options.credentials, "same-origin");
});

for (const writing of [false, true]) {
  test(`network failure preserves uncertainty only for writes (${writing})`, async (t) => {
    let calls = 0;
    t.mock.method(globalThis, "fetch", async () => {
      calls++;
      throw new TypeError("offline");
    });
    await assert.rejects(request("/api/test", writing ? {} : undefined), (error) => {
      assert.ok(error instanceof APIError);
      assert.equal(error.code, "network_error");
      assert.equal(error.uncertain, writing);
      assert.equal(requiresReload(error, true), writing);
      return true;
    });
    assert.equal(calls, 1);
  });
}

test("slow request aborts and requires reload before another write", async (t) => {
  t.mock.method(
    globalThis,
    "fetch",
    (_path, { signal }) =>
      new Promise((_resolve, reject) => {
        signal.addEventListener("abort", () => reject(new DOMException("timeout", "AbortError")));
      }),
  );
  await assert.rejects(request("/api/test", {}, { timeoutMs: 5 }), (error) => {
    assert.equal(error.code, "request_timeout");
    assert.equal(requiresReload(error, true), true);
    assert.equal(requiresReload(error, false), false);
    return true;
  });
});

for (const [status, code, reload] of [
  [400, "invalid_action", false],
  [409, "revision_conflict", true],
  [500, "internal_error", true],
  [503, "storage_unavailable", true],
]) {
  test(`HTTP ${status} handles whether the write can be confirmed`, async (t) => {
    t.mock.method(globalThis, "fetch", async () => json({ error: { code } }, status));
    await assert.rejects(request("/api/test", {}), (error) => {
      assert.equal(error.status, status);
      assert.equal(error.code, code);
      assert.equal(requiresReload(error, true), reload);
      return true;
    });
  });
}

for (const kind of ["html", "broken_json", "null", "primitive"]) {
  test(`invalid ${kind} response does not confirm a write`, async (t) => {
    t.mock.method(globalThis, "fetch", async () => {
      if (kind === "html") return new Response("<html>proxy failed</html>", { status: 502 });
      if (kind === "broken_json")
        return new Response("{", { headers: { "content-type": "application/json" } });
      return json(kind === "null" ? null : "wrong");
    });
    await assert.rejects(request("/api/test", {}), (error) => {
      assert.equal(error.code, "invalid_response");
      assert.equal(requiresReload(error, true), true);
      return true;
    });
  });
}

test("GET arrays remain valid and cannot trigger write recovery", async (t) => {
  t.mock.method(globalThis, "fetch", async () => json([{ id: "public-example" }]));
  assert.deepEqual(await request("/api/examples"), [{ id: "public-example" }]);
  assert.equal(requiresReload(new Error("local failure"), true), false);
});
