import {
  getStatusLabel,
  isDocumentStatus,
} from "../../features/documents/model/statuses";

export function StatusBadge({ status }: { status: string }) {
  const normalizedStatus = isDocumentStatus(status) ? status : "FAILED";
  return (
    <span className={`status-badge ${normalizedStatus.toLowerCase()}`}>
      {getStatusLabel(status)}
    </span>
  );
}
