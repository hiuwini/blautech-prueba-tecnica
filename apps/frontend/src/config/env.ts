const DEFAULT_DOCUMENT_PROCESSING_BASE_URL = "http://localhost:8000";
const DEFAULT_BFF_BASE_URL = "http://localhost:4000";
const DEFAULT_SOCKET_IO_NAMESPACE = "/notifications";

export interface FrontendConfig {
  documentProcessingBaseUrl: string;
  bffBaseUrl: string;
  socketNamespace: string;
}

export function loadFrontendConfig(): FrontendConfig {
  return {
    documentProcessingBaseUrl: normalizeBaseUrl(
      import.meta.env.VITE_DOCUMENT_PROCESSING_BASE_URL,
      DEFAULT_DOCUMENT_PROCESSING_BASE_URL,
    ),
    bffBaseUrl: normalizeBaseUrl(
      import.meta.env.VITE_BFF_BASE_URL,
      DEFAULT_BFF_BASE_URL,
    ),
    socketNamespace: normalizeNamespace(
      import.meta.env.VITE_SOCKET_IO_NAMESPACE ?? DEFAULT_SOCKET_IO_NAMESPACE,
    ),
  };
}

function normalizeBaseUrl(value: string | undefined, fallback: string): string {
  const rawValue = typeof value === "string" && value.trim() ? value.trim() : fallback;
  return rawValue.replace(/\/+$/, "");
}

function normalizeNamespace(value: string): string {
  const namespace = value.trim() || DEFAULT_SOCKET_IO_NAMESPACE;
  return namespace.startsWith("/") ? namespace : `/${namespace}`;
}
