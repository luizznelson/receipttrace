export class APIError extends Error {
  constructor(code, status) {
    super(code);
    this.code = code;
    this.status = status;
  }
}

export async function request(path, data) {
  const response = await fetch(path, {
    method: data === undefined ? "GET" : "POST",
    headers:
      data === undefined
        ? { Accept: "application/json" }
        : { Accept: "application/json", "Content-Type": "application/json" },
    credentials: "same-origin",
    ...(data === undefined ? {} : { body: JSON.stringify(data) }),
  });
  const payload = await response.json();
  if (!response.ok) throw new APIError(payload.error?.code ?? "generic", response.status);
  return payload;
}
