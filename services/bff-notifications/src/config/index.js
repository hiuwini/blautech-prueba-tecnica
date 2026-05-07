const DEFAULT_FRONTEND_BASE_URL = "http://localhost:3000";
const DEFAULT_FASTAPI_BASE_URL = "http://document-processing:8000";

export function loadConfig(env = process.env) {
  const frontendBaseUrl = getString(
    env.FRONTEND_BASE_URL,
    DEFAULT_FRONTEND_BASE_URL,
  );

  return {
    host: getString(env.BFF_HOST, "0.0.0.0"),
    port: getInt(env.BFF_PORT, 4000),
    serviceName: "bff-notifications",
    frontendBaseUrl,
    corsAllowedOrigins: getCsv(env.BFF_CORS_ALLOWED_ORIGINS, [
      frontendBaseUrl,
    ]),
    socketNamespace: normalizeNamespace(
      getString(env.SOCKET_IO_NAMESPACE, "/notifications"),
    ),
    fastapiBaseUrl: getString(env.FASTAPI_BASE_URL, DEFAULT_FASTAPI_BASE_URL),
    fastapiTimeoutMs: getFloat(env.BFF_FASTAPI_TIMEOUT_SECONDS, 3) * 1000,
    dashboardPageSize: getInt(env.BFF_DASHBOARD_PAGE_SIZE, 100),
    dashboardMaxDocuments: getInt(env.BFF_DASHBOARD_MAX_DOCUMENTS, 500),
  };
}

function getString(value, fallback) {
  return typeof value === "string" && value.trim() ? value.trim() : fallback;
}

function getInt(value, fallback) {
  if (typeof value !== "string" || !value.trim()) {
    return fallback;
  }

  const parsed = Number.parseInt(value, 10);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
}

function getFloat(value, fallback) {
  if (typeof value !== "string" || !value.trim()) {
    return fallback;
  }

  const parsed = Number.parseFloat(value);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
}

function getCsv(value, fallback) {
  if (typeof value !== "string" || !value.trim()) {
    return fallback;
  }

  const items = value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);

  return items.length > 0 ? items : fallback;
}

function normalizeNamespace(value) {
  return value.startsWith("/") ? value : `/${value}`;
}
