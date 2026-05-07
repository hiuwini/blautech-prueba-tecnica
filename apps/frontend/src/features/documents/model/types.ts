export type DocumentStatus =
  | "UPLOADED"
  | "PROCESSING"
  | "COMPLIANT"
  | "NON_COMPLIANT"
  | "FAILED";

export interface ComplianceCheck {
  document_id: string;
  status: DocumentStatus | string;
  check_id: string;
  details: string | null;
  checked_at: string;
}

export interface RegulatoryDocument {
  document_id: string;
  user_id: string | null;
  document_type: string;
  original_filename: string;
  content_type: string;
  size_bytes: number;
  bucket_name: string;
  object_key: string;
  status: DocumentStatus;
  created_at: string;
  updated_at: string;
  processed_at: string | null;
  latest_compliance_check: ComplianceCheck | null;
}

export interface DocumentListResponse {
  items: RegulatoryDocument[];
  total: number;
  limit: number;
  offset: number;
}

export interface ProcessDocumentResponse {
  document: RegulatoryDocument;
  compliance_check: ComplianceCheck | null;
  notification_sent: boolean | null;
}

export interface DownloadUrlResponse {
  document_id: string;
  url: string;
  expires_in_seconds: number;
}
