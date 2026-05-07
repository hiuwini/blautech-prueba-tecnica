import type { DocumentStatus } from "./types";

export const DOCUMENT_STATUSES: DocumentStatus[] = [
  "UPLOADED",
  "PROCESSING",
  "COMPLIANT",
  "NON_COMPLIANT",
  "FAILED",
];

export const DOCUMENT_STATUS_LABELS: Record<DocumentStatus, string> = {
  UPLOADED: "Cargado",
  PROCESSING: "Procesando",
  COMPLIANT: "Cumple",
  NON_COMPLIANT: "No cumple",
  FAILED: "Fallido",
};

export const DOCUMENT_TYPES = [
  { value: "financial_report", label: "Financial report" },
  { value: "tax_filing", label: "Tax filing" },
  { value: "regulatory_disclosure", label: "Regulatory disclosure" },
] as const;

export function getStatusLabel(status: string): string {
  if (isDocumentStatus(status)) {
    return DOCUMENT_STATUS_LABELS[status];
  }
  return status;
}

export function isDocumentStatus(status: string): status is DocumentStatus {
  return DOCUMENT_STATUSES.includes(status as DocumentStatus);
}

export function formatDocumentType(documentType: string): string {
  return documentType
    .split("_")
    .filter(Boolean)
    .map((item) => item.charAt(0).toUpperCase() + item.slice(1))
    .join(" ");
}
