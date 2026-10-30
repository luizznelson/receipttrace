import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { messages, translate } from "../../src/receipttrace/static/i18n.js";
import { changesFor, valueText, formatNumber } from "../../src/receipttrace/static/ui.js";

test("both languages cover all labels used by the page", () => {
  const html = readFileSync(
    new URL("../../src/receipttrace/static/index.html", import.meta.url),
    "utf8",
  );
  const keys = [...html.matchAll(/data-i18n(?:-aria|-alt|-placeholder)?="([^"]+)"/g)].map(
    (match) => match[1],
  );
  assert.deepEqual(Object.keys(messages.pt), Object.keys(messages.en));
  for (const lang of ["pt", "en"]) for (const key of keys) assert.ok(translate(lang, key).trim());
});
test("status labels keep extraction, arithmetic and review separate", () => {
  for (const lang of ["pt", "en"]) {
    const values = ["extraction_ok", "arithmetic_not_checked", "review_completed"].map((key) =>
      translate(lang, key),
    );
    assert.equal(new Set(values).size, 3);
    for (const key of ["partial", "passed", "findings", "not_checked", "unavailable"])
      assert.ok(translate(lang, "arithmetic_" + key));
  }
});
test("receipt value formatting preserves the original writing", () => {
  for (const value of ["61,799", "3.600.000", "0001", "-38,500", "٣٥", "Rp 1.000"])
    assert.equal(valueText(value, "missing"), value);
  assert.equal(valueText(null, "missing"), "missing");
  assert.equal(valueText(0, "missing"), "0");
});
test("a correction uses the current revision value, not the extraction original", () => {
  assert.deepEqual(changesFor({ total: "61,799" }, { total: "61,799" }), []);
  assert.deepEqual(changesFor({ total: "62,000" }, { total: "61,799" }), [
    { path: "/total", value: "61,799" },
  ]);
});
test("blank edited fields become null without filling other missing fields", () => {
  assert.deepEqual(changesFor({ total: "61,799", tax: null }, { total: "  ", tax: "" }), [
    { path: "/total", value: null },
  ]);
});
test("correction payload preserves text instead of converting money to floating point", () => {
  assert.deepEqual(changesFor({ total: "0" }, { total: "123456789012345678" }), [
    { path: "/total", value: "123456789012345678" },
  ]);
});
test("only indicator numbers use the selected locale", () => {
  assert.equal(formatNumber("pt", 8.33), "8,33");
  assert.equal(formatNumber("en", 8.33), "8.33");
  assert.equal(translate("pt", "ratio", { n: 19, d: 19 }), "19 de 19");
  assert.equal(translate("en", "ratio", { n: 19, d: 19 }), "19 of 19");
});
test("missing translations fail explicitly during verification", () => {
  assert.throws(() => translate("pt", "missing_label"), /Missing translation/);
});
