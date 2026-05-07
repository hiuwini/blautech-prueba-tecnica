import type { DocumentStatus } from "../../documents/model/types";

export interface DocumentStatusChangedEvent {
  document_id: string;
  status: DocumentStatus;
  document_type: string;
  checked_at: string;
}
