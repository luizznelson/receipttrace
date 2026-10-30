export class APIError extends Error {
  constructor(code, status, { uncertain = false } = {}) {
    super(code);
    this.code = code;
    this.status = status;
    this.uncertain = uncertain;
  }
}

export const REQUEST_TIMEOUT_MS = 15000;
export function requiresReload(error, hasReview) {
  return Boolean(
    hasReview &&
    error instanceof APIError &&
    (error.code === "revision_conflict" || error.uncertain),
  );
}

export async function request(path, data, { timeoutMs = REQUEST_TIMEOUT_MS } = {}) {
  const writing = data !== undefined;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(path, {
      method: writing ? "POST" : "GET",
      headers: writing
        ? { Accept: "application/json", "Content-Type": "application/json" }
        : { Accept: "application/json" },
      credentials: "same-origin",
      signal: controller.signal,
      ...(writing ? { body: JSON.stringify(data) } : {}),
    });
    if (!response.headers.get("content-type")?.toLowerCase().includes("application/json")) {
      throw new APIError("invalid_response", response.status, { uncertain: writing });
    }
    let payload;
    try {
      payload = await response.json();
    } catch (error) {
      if (controller.signal.aborted) throw error;
      throw new APIError("invalid_response", response.status, { uncertain: writing });
    }
    if (payload === null || typeof payload !== "object") {
      throw new APIError("invalid_response", response.status, { uncertain: writing });
    }
    if (!response.ok) {
      throw new APIError(payload.error?.code ?? "generic", response.status, {
        uncertain: writing && response.status >= 500,
      });
    }
    return payload;
  } catch (error) {
    if (error instanceof APIError) throw error;
    throw new APIError(controller.signal.aborted ? "request_timeout" : "network_error", 0, {
      uncertain: writing,
    });
  } finally {
    clearTimeout(timer);
  }
}
