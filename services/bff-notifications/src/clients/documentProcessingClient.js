export class UpstreamDashboardError extends Error {
  constructor(message, options = {}) {
    super(message, options);
    this.name = "UpstreamDashboardError";
  }
}

export async function fetchDocumentsPage(
  config,
  fetchImpl = globalThis.fetch,
  { limit, offset },
) {
  if (typeof fetchImpl !== "function") {
    throw new UpstreamDashboardError("Fetch API is not available");
  }

  const url = new URL("/api/v1/documents", config.fastapiBaseUrl);
  url.searchParams.set("limit", String(limit));
  url.searchParams.set("offset", String(offset));

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), config.fastapiTimeoutMs);

  try {
    const response = await fetchImpl(url, {
      headers: {
        Accept: "application/json",
      },
      signal: controller.signal,
    });

    if (!response.ok) {
      throw new UpstreamDashboardError(
        `Document Processing returned HTTP ${response.status}`,
      );
    }

    const payload = await response.json();
    if (!isPlainObject(payload) || !Array.isArray(payload.items)) {
      throw new UpstreamDashboardError(
        "Document Processing returned invalid JSON",
      );
    }

    return {
      items: payload.items,
      total: Number.isInteger(payload.total) ? payload.total : payload.items.length,
    };
  } catch (error) {
    if (error instanceof UpstreamDashboardError) {
      throw error;
    }

    throw new UpstreamDashboardError(
      "Document Processing is unavailable",
      { cause: error },
    );
  } finally {
    clearTimeout(timeout);
  }
}

function isPlainObject(value) {
  return (
    value !== null &&
    typeof value === "object" &&
    !Array.isArray(value)
  );
}
