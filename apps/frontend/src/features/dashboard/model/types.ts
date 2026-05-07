import type { DocumentStatus } from "../../documents/model/types";

export interface DashboardRecentDocument {
  document_id: string | null;
  document_type: string | null;
  original_filename: string | null;
  status: DocumentStatus | string | null;
  updated_at: string | null;
  processed_at: string | null;
}

export interface DashboardSummary {
  total_documents: number;
  aggregated_documents: number;
  is_complete: boolean;
  by_status: Record<DocumentStatus, number>;
  by_document_type: Record<string, number>;
  recent_documents: DashboardRecentDocument[];
  source: string;
}
