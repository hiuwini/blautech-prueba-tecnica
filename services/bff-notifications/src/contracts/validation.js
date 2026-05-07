import { FINAL_DOCUMENT_STATUSES } from "./statuses.js";

const UUID_PATTERN =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const ISO_UTC_PATTERN =
  /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$/;

export function validateProcessingCompletePayload(payload) {
  if (!isPlainObject(payload)) {
    return {
      ok: false,
      errors: ["JSON object body is required"],
    };
  }

  const errors = [];
  const documentId = normalizeString(payload.document_id);
  const status = normalizeString(payload.status);
  const documentType = normalizeString(payload.document_type);
  const checkedAt = normalizeString(payload.checked_at);

  if (!documentId) {
    errors.push("document_id is required");
  } else if (!UUID_PATTERN.test(documentId)) {
    errors.push("document_id must be a valid UUID");
  }

  if (!status) {
    errors.push("status is required");
  } else if (!FINAL_DOCUMENT_STATUSES.includes(status)) {
    errors.push(
      `status must be one of ${FINAL_DOCUMENT_STATUSES.join(", ")}`,
    );
  }

  if (!documentType) {
    errors.push("document_type is required");
  }

  if (!checkedAt) {
    errors.push("checked_at is required");
  } else if (!isIsoUtcTimestamp(checkedAt)) {
    errors.push("checked_at must be an ISO 8601 UTC timestamp");
  }

  if (errors.length > 0) {
    return { ok: false, errors };
  }

  return {
    ok: true,
    payload: {
      document_id: documentId,
      status,
      document_type: documentType,
      checked_at: checkedAt,
    },
  };
}

export function toDocumentStatusChangedEvent(payload) {
  return {
    document_id: payload.document_id,
    status: payload.status,
    document_type: payload.document_type,
    checked_at: payload.checked_at,
  };
}

function isPlainObject(value) {
  return (
    value !== null &&
    typeof value === "object" &&
    !Array.isArray(value)
  );
}

function normalizeString(value) {
  return typeof value === "string" && value.trim() ? value.trim() : "";
}

function isIsoUtcTimestamp(value) {
  return ISO_UTC_PATTERN.test(value) && !Number.isNaN(Date.parse(value));
}
