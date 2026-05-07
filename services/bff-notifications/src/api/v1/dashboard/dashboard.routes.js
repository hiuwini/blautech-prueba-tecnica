import express from "express";

import { createDashboardController } from "../../../controllers/dashboardController.js";

export function createDashboardRouter({ config, dashboardSummaryProvider }) {
  const router = express.Router();
  const controller = createDashboardController({
    config,
    dashboardSummaryProvider,
  });

  router.get("/summary", controller.getSummary);

  return router;
}
