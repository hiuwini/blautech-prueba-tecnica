import { Eye, FileText, Play } from "lucide-react";

import { StatusBadge } from "../../../shared/ui/StatusBadge";
import { formatBytes, formatDate } from "../../../shared/utils/format";
import { formatDocumentType } from "../model/statuses";
import type { RegulatoryDocument } from "../model/types";

export function DocumentTable({
  documents,
  isLoading,
  processingIds,
  selectedDocumentId,
  onSelect,
  onProcess,
}: {
  documents: RegulatoryDocument[];
  isLoading: boolean;
  processingIds: Set<string>;
  selectedDocumentId: string | null;
  onSelect: (documentId: string) => void;
  onProcess: (documentId: string) => void;
}) {
  if (isLoading && documents.length === 0) {
    return <div className="empty-state">Cargando documentos...</div>;
  }

  if (documents.length === 0) {
    return <div className="empty-state">Sin documentos</div>;
  }

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Archivo</th>
            <th>Tipo</th>
            <th>Estado</th>
            <th>Actualizado</th>
            <th aria-label="Acciones" />
          </tr>
        </thead>
        <tbody>
          {documents.map((document) => {
            const isProcessing = processingIds.has(document.document_id);
            return (
              <tr
                key={document.document_id}
                className={
                  selectedDocumentId === document.document_id
                    ? "selected-row"
                    : undefined
                }
              >
                <td>
                  <div className="file-cell">
                    <FileText aria-hidden="true" size={18} />
                    <div>
                      <strong>{document.original_filename}</strong>
                      <span>{formatBytes(document.size_bytes)}</span>
                    </div>
                  </div>
                </td>
                <td>{formatDocumentType(document.document_type)}</td>
                <td>
                  <StatusBadge status={document.status} />
                </td>
                <td>{formatDate(document.updated_at)}</td>
                <td>
                  <div className="row-actions">
                    <button
                      className="icon-only-button"
                      type="button"
                      onClick={() => onSelect(document.document_id)}
                      aria-label={`Ver detalle de ${document.original_filename}`}
                      title="Detalle"
                    >
                      <Eye aria-hidden="true" size={17} />
                    </button>
                    <button
                      className="icon-only-button"
                      type="button"
                      onClick={() => onProcess(document.document_id)}
                      disabled={isProcessing || document.status === "PROCESSING"}
                      aria-label={`Procesar ${document.original_filename}`}
                      title="Procesar"
                    >
                      <Play aria-hidden="true" size={17} />
                    </button>
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
