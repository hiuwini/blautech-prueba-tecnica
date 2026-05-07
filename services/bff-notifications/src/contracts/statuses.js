export const UPLOADED = "UPLOADED";
export const PROCESSING = "PROCESSING";
export const COMPLIANT = "COMPLIANT";
export const NON_COMPLIANT = "NON_COMPLIANT";
export const FAILED = "FAILED";

export const DOCUMENT_STATUSES = Object.freeze([
  UPLOADED,
  PROCESSING,
  COMPLIANT,
  NON_COMPLIANT,
  FAILED,
]);

export const FINAL_DOCUMENT_STATUSES = Object.freeze([
  COMPLIANT,
  NON_COMPLIANT,
  FAILED,
]);
