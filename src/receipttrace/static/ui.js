// Untrusted receipt text, actor names and notes always become text nodes, never HTML.
export function element(tag, attributes = {}, ...children) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attributes)) {
    if (value !== null && value !== undefined) node.setAttribute(key, String(value));
  }
  for (const child of children.flat()) {
    if (child !== null && child !== undefined)
      node.append(child instanceof Node ? child : document.createTextNode(String(child)));
  }
  return node;
}

export const fieldNames = ["total", "subtotal", "tax", "service", "discount"];
export const valueText = (value, empty) =>
  value === null || value === undefined || value === "" ? empty : String(value);
export const numericLocale = (lang) => (lang === "pt" ? "pt-BR" : "en-US");
export const formatNumber = (lang, value, digits = 2) =>
  new Intl.NumberFormat(numericLocale(lang), {
    maximumFractionDigits: digits,
    minimumFractionDigits: digits,
  }).format(value);
export function changesFor(raw, draft) {
  return fieldNames.flatMap((name) => {
    const value = String(draft[name] ?? "");
    const after = value.trim() === "" ? null : value;
    return after === (raw[name] ?? null) ? [] : [{ path: `/${name}`, value: after }];
  });
}
