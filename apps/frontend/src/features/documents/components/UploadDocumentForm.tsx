import { Upload } from "lucide-react";
import type { ChangeEvent, DragEvent, FormEvent } from "react";

import type { LoadState } from "../../../shared/ui/LoadState";
import { DOCUMENT_TYPES } from "../model/statuses";

export function UploadDocumentForm({
  documentType,
  selectedFile,
  isDraggingFile,
  uploadState,
  onDocumentTypeChange,
  onFileChange,
  onSubmit,
  onDragOver,
  onDragLeave,
  onDrop,
}: {
  documentType: string;
  selectedFile: File | null;
  isDraggingFile: boolean;
  uploadState: LoadState;
  onDocumentTypeChange: (documentType: string) => void;
  onFileChange: (event: ChangeEvent<HTMLInputElement>) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  onDragOver: (event: DragEvent<HTMLDivElement>) => void;
  onDragLeave: (event: DragEvent<HTMLDivElement>) => void;
  onDrop: (event: DragEvent<HTMLDivElement>) => void;
}) {
  return (
    <section className="panel" aria-labelledby="upload-title">
      <div className="panel-header">
        <h2 id="upload-title">Upload</h2>
      </div>
      <div
        className={`drop-zone${isDraggingFile ? " drop-zone-active" : ""}`}
        onDragOver={onDragOver}
        onDragEnter={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
        role="presentation"
        data-testid="upload-dropzone"
      >
        <p className="drop-zone-hint">
          {selectedFile
            ? `Listo para subir: ${selectedFile.name}`
            : "Arrastra un archivo aqui o usa el selector"}
        </p>
        <form className="upload-form" onSubmit={onSubmit}>
          <label className="field">
            <span>Tipo</span>
            <select
              value={documentType}
              onChange={(event) => onDocumentTypeChange(event.target.value)}
            >
              {DOCUMENT_TYPES.map((type) => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </select>
          </label>
          <label className="field file-field">
            <span>Archivo</span>
            <input type="file" onChange={onFileChange} />
          </label>
          <button
            className="primary-button"
            type="submit"
            disabled={uploadState === "loading"}
          >
            <Upload aria-hidden="true" size={18} />
            <span>{uploadState === "loading" ? "Subiendo" : "Subir"}</span>
          </button>
        </form>
      </div>
    </section>
  );
}
