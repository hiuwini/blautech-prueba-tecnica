import { loadFrontendConfig } from "../../../config/env";

const config = loadFrontendConfig();

export function getSocketUrl(): string {
  return `${config.bffBaseUrl}${config.socketNamespace}`;
}
