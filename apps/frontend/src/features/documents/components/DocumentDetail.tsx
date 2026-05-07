import { Play } from "lucide-react";

import { StatusBadge } from "../../../shared/ui/StatusBadge";
import type { LoadState, LoadStateProps } from "../../../shared/ui/LoadState";
import { formatBytes, formatDate } from "../../../shared/utils/format";
import { formatDocumentType, getStatusLabel } from "../model/statuses";
import type { RegulatoryDocument } from "../model/types";
import { DownloadDocumentAction } from "./DownloadDocumentAction";

export function DocumentDetail({
  document,
  state,
  downloadUrl,
  downloadState,
  isProcessing,
  onProcess,
  onDownload,
}: {
  document: RegulatoryDocument | null;
  downloadUrl: string | null;
  downloadState: LoadState;
  isProcessing: boolean;
  onProcess: (documentId: string) => void;
  onDownload: (documentId: string) => void;
} & LoadStateProps) {
  return (
    <section className="panel detail-panel" aria-labelledby="detail-title">
      <div className="panel-header">
        <h2 id="detail-title">Detalle</h2>
      </div>

      {state === "loading" && !document ? (
        <div className="empty-state">Cargando detalle...</div>
      ) : null}

      {!document && state !== "loading" ? (
        <div className="empty-state">Selecciona un documento</div>
      ) : null}

      {document ? (
        <div className="detail-content">
          <div className="detail-title-row">
            <div>
              <h3>{document.original_filename}</h3>
              <p>{document.document_id}</p>
            </div>
            <StatusBadge status={document.status} />
          </div>

          <dl className="metadata-grid">
            <div>
              <dt>Tipo</dt>
              <dd>{formatDocumentType(document.document_type)}</dd>
            </div>
            <div>
              <dt>Tamano</dt>
              <dd>{formatBytes(document.size_bytes)}</dd>
            </div>
            <div>
              <dt>Content type</dt>
              <dd>{document.content_type}</dd>
            </div>
            <div>
              <dt>Creado</dt>
              <dd>{formatDate(document.created_at)}</dd>
            </div>
            <div>
              <dt>Procesado</dt>
              <dd>
                {document.processed_at
                  ? formatDate(document.processed_at)
                  : "Pendiente"}
              </dd>
            </div>
            <div>
              <dt>Object key</dt>
              <dd>{document.object_key}</dd>
            </div>
          </dl>

          <div className="compliance-box">
            <h4>Compliance</h4>
            {document.latest_compliance_check ? (
              <dl className="metadata-grid compact">
                <div>
                  <dt>Estado</dt>
                  <dd>{getStatusLabel(document.latest_compliance_check.status)}</dd>
                </div>
                <div>
                  <dt>Check ID</dt>
                  <dd>
                    {document.latest_compliance_check.check_id || "No disponible"}
                  </dd>
                </div>
                <div>
                  <dt>Fecha</dt>
                  <dd>{formatDate(document.latest_compliance_check.checked_at)}</dd>
                </div>
                <div>
                  <dt>Detalle</dt>
                  <dd>{document.latest_compliance_check.details ?? "Sin detalle"}</dd>
                </div>
              </dl>
            ) : (
              <p className="muted">Sin resultado</p>
            )}
          </div>

          <div className="detail-actions">
            <button
              className="primary-button"
              type="button"
              onClick={() => onProcess(document.document_id)}
              disabled={isProcessing || document.status === "PROCESSING"}
            >
              <Play aria-hidden="true" size={18} />
              <span>{isProcessing ? "Procesando" : "Procesar"}</span>
            </button>
            <DownloadDocumentAction
              documentId={document.document_id}
              downloadUrl={downloadUrl}
              downloadState={downloadState}
              onDownload={onDownload}
            />
          </div>
        </div>
      ) : null}
    </section>
  );
}
