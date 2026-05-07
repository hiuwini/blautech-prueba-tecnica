import {
  fetchDashboardSummary,
  UpstreamDashboardError,
} from "../services/dashboardSummaryService.js";

export function createDashboardController({ config, dashboardSummaryProvider }) {
  const getDashboardSummary =
    dashboardSummaryProvider ?? (() => fetchDashboardSummary(config));

  return {
    async getSummary(_request, response) {
      try {
        const summary = await getDashboardSummary();
        response.json(summary);
      } catch (error) {
        const statusCode = error instanceof UpstreamDashboardError ? 502 : 500;
        response.status(statusCode).json({
          error: "UPSTREAM_UNAVAILABLE",
          message: "Unable to fetch dashboard data from Document Processing",
        });
      }
    },
  };
}
