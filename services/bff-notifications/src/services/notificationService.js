export const DOCUMENT_STATUS_CHANGED_EVENT = "document-status-changed";

export function emitDocumentStatusChanged(notificationsNamespace, eventPayload) {
  notificationsNamespace.emit(DOCUMENT_STATUS_CHANGED_EVENT, eventPayload);

  return {
    status: "accepted",
    event: DOCUMENT_STATUS_CHANGED_EVENT,
    document_id: eventPayload.document_id,
  };
}
