/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_DOCUMENT_PROCESSING_BASE_URL?: string;
  readonly VITE_BFF_BASE_URL?: string;
  readonly VITE_SOCKET_IO_NAMESPACE?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
