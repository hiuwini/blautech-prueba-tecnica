import {
  toDocumentStatusChangedEvent,
  validateProcessingCompletePayload,
} from "../contracts/validation.js";
import { emitDocumentStatusChanged } from "../services/notificationService.js";

export function createWebhookController() {
  return {
    processingComplete(request, response) {
      const validation = validateProcessingCompletePayload(request.body);
      if (!validation.ok) {
        response.status(400).json({
          error: "INVALID_REQUEST",
          message: "Webhook payload is invalid",
          details: validation.errors,
        });
        return;
      }

      const eventPayload = toDocumentStatusChangedEvent(validation.payload);
      const acceptedPayload = emitDocumentStatusChanged(
        request.app.locals.notificationsNamespace,
        eventPayload,
      );

      response.status(202).json(acceptedPayload);
    },
  };
}
