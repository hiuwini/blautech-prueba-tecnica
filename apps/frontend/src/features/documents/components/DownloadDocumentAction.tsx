import { Download } from "lucide-react";

import type { LoadState } from "../../../shared/ui/LoadState";

export function DownloadDocumentAction({
  documentId,
  downloadUrl,
  downloadState,
  onDownload,
}: {
  documentId: string;
  downloadUrl: string | null;
  downloadState: LoadState;
  onDownload: (documentId: string) => void;
}) {
  return (
    <>
      <button
        className="secondary-button"
        type="button"
        onClick={() => onDownload(documentId)}
        disabled={downloadState === "loading"}
      >
        <Download aria-hidden="true" size={18} />
        <span>{downloadState === "loading" ? "Generando" : "Descarga"}</span>
      </button>

      {downloadUrl ? (
        <a
          className="download-link"
          href={downloadUrl}
          target="_blank"
          rel="noreferrer"
        >
          Abrir enlace de descarga
        </a>
      ) : null}
    </>
  );
}
