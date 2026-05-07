import { loadFrontendConfig } from "../../../config/env";
import { apiUrl, requestJson } from "../../../shared/api/http";
import type { DashboardSummary } from "../model/types";

const config = loadFrontendConfig();

export async function fetchDashboardSummary(): Promise<DashboardSummary> {
  return requestJson<DashboardSummary>(
    apiUrl(config.bffBaseUrl, "/api/v1/dashboard/summary"),
    {
      headers: {
        Accept: "application/json",
      },
    },
  );
}
