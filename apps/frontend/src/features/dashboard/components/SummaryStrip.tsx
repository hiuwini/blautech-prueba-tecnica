import {
  DOCUMENT_STATUS_LABELS,
  DOCUMENT_STATUSES,
} from "../../documents/model/statuses";
import type { DocumentStatus } from "../../documents/model/types";

export function SummaryStrip({
  totalDocuments,
  statusCounts,
  loading,
}: {
  totalDocuments: number;
  statusCounts: Record<DocumentStatus, number>;
  loading: boolean;
}) {
  return (
    <div className="summary-strip">
      <SummaryMetric label="Total" value={totalDocuments} loading={loading} />
      {DOCUMENT_STATUSES.map((status) => (
        <SummaryMetric
          key={status}
          label={DOCUMENT_STATUS_LABELS[status]}
          value={statusCounts[status] ?? 0}
          loading={loading}
        />
      ))}
    </div>
  );
}

function SummaryMetric({
  label,
  value,
  loading,
}: {
  label: string;
  value: number;
  loading: boolean;
}) {
  return (
    <div className="summary-metric">
      <span>{label}</span>
      <strong>{loading ? "..." : value}</strong>
    </div>
  );
}
