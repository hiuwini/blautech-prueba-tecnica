import { formatDocumentType } from "../../documents/model/statuses";
import type { DashboardSummary } from "../model/types";

export function TypeSummary({ summary }: { summary: DashboardSummary | null }) {
  const entries = Object.entries(summary?.by_document_type ?? {}).slice(0, 4);

  return (
    <div className="type-summary" aria-label="Documentos por tipo">
      {entries.length === 0 ? (
        <span className="muted">Sin tipos registrados</span>
      ) : (
        entries.map(([type, count]) => (
          <span key={type}>
            {formatDocumentType(type)}
            <strong>{count}</strong>
          </span>
        ))
      )}
    </div>
  );
}
