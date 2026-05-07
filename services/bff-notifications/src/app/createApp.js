import express from "express";

import { createHealthRouter } from "../api/health.routes.js";
import { createDashboardRouter } from "../api/v1/dashboard/dashboard.routes.js";
import { createProcessingCompleteWebhookRouter } from "../api/v1/webhooks/processingComplete.routes.js";
import { loadConfig } from "../config/index.js";
import { createCorsMiddleware } from "../middleware/cors.js";
import { errorHandler } from "../middleware/errorHandler.js";
import { notFoundHandler } from "../middleware/notFound.js";

export function createApp({ config, dashboardSummaryProvider } = {}) {
  const appConfig = config ?? loadConfig();
  const app = express();

  app.disable("x-powered-by");
  app.use(createCorsMiddleware(appConfig.corsAllowedOrigins));
  app.use(express.json({ limit: "1mb" }));

  app.use(createHealthRouter(appConfig));
  app.use(
    "/api/v1/dashboard",
    createDashboardRouter({
      config: appConfig,
      dashboardSummaryProvider,
    }),
  );
  app.use(
    "/api/v1/webhooks",
    createProcessingCompleteWebhookRouter(),
  );

  app.use(notFoundHandler);
  app.use(errorHandler);

  return app;
}
