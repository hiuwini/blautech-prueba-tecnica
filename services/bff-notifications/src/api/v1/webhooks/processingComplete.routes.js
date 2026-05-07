import express from "express";

import { createWebhookController } from "../../../controllers/webhookController.js";

export function createProcessingCompleteWebhookRouter() {
  const router = express.Router();
  const controller = createWebhookController();

  router.post("/processing-complete", controller.processingComplete);

  return router;
}
