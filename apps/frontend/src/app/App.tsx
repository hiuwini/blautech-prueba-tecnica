import { RefreshCw } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import type { ChangeEvent, DragEvent, FormEvent } from "react";

import { fetchDashboardSummary } from "../features/dashboard/api/dashboardApi";
import { StatusBarChart } from "../features/dashboard/components/StatusBarChart";
import { SummaryStrip } from "../features/dashboard/components/SummaryStrip";
import { TypeSummary } from "../features/dashboard/components/TypeSummary";
import type { DashboardSummary } from "../features/dashboard/model/types";
import {
  getDocument,
  getDownloadUrl,
  listDocuments,
  processDocument,
  uploadDocument,
} from "../features/documents/api/documentsApi";
import { DocumentDetail } from "../features/documents/components/DocumentDetail";
import { DocumentTable } from "../features/documents/components/DocumentTable";
import { UploadDocumentForm } from "../features/documents/components/UploadDocumentForm";
import { DOCUMENT_STATUSES, DOCUMENT_TYPES } from "../features/documents/model/statuses";
import type {
  DocumentStatus,
  RegulatoryDocument,
} from "../features/documents/model/types";
import { NotificationsPanel } from "../features/notifications/components/NotificationsPanel";
import { SocketIndicator } from "../features/notifications/components/SocketIndicator";
import { useDocumentNotifications } from "../features/notifications/hooks/useDocumentNotifications";
import type { DocumentStatusChangedEvent } from "../features/notifications/model/types";
import { ApiError } from "../shared/api/http";
import type { LoadState } from "../shared/ui/LoadState";
import { isRecord, toDisplayError } from "../shared/utils/errors";

const PAGE_SIZE = 50;

function App() {
  const [documents, setDocuments] = useState<RegulatoryDocument[]>([]);
  const [totalDocuments, setTotalDocuments] = useState(0);
  const [selectedDocumentId, setSelectedDocumentId] = useState<string | null>(null);
  const [selectedDocument, setSelectedDocument] =
    useState<RegulatoryDocument | null>(null);
  const [dashboardSummary, setDashboardSummary] =
    useState<DashboardSummary | null>(null);
  const [notifications, setNotifications] = useState<DocumentStatusChangedEvent[]>([]);
  const [documentType, setDocumentType] = useState<string>(DOCUMENT_TYPES[0].value);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDraggingFile, setIsDraggingFile] = useState(false);
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null);
  const [listState, setListState] = useState<LoadState>("idle");
  const [detailState, setDetailState] = useState<LoadState>("idle");
  const [dashboardState, setDashboardState] = useState<LoadState>("idle");
  const [uploadState, setUploadState] = useState<LoadState>("idle");
  const [downloadState, setDownloadState] = useState<LoadState>("idle");
  const [processingIds, setProcessingIds] = useState<Set<string>>(() => new Set());
  const [pageError, setPageError] = useState<string | null>(null);

  const refreshDashboard = useCallback(async () => {
    setDashboardState("loading");
    try {
      const summary = await fetchDashboardSummary();
      setDashboardSummary(summary);
      setDashboardState("success");
    } catch (error) {
      setDashboardState("error");
      setPageError(toDisplayError(error));
    }
  }, []);

  const refreshDocuments = useCallback(async () => {
    setListState("loading");
    try {
      const response = await listDocuments(PAGE_SIZE, 0);
      setDocuments(response.items);
      setTotalDocuments(response.total);
      setListState("success");
      setPageError(null);
    } catch (error) {
      setListState("error");
      setPageError(toDisplayError(error));
    }
  }, []);

  const loadDocument = useCallback(async (documentId: string) => {
    setDetailState("loading");
    setDownloadUrl(null);
    try {
      const document = await getDocument(documentId);
      setSelectedDocument(document);
      setDetailState("success");
      setPageError(null);
    } catch (error) {
      setDetailState("error");
      setPageError(toDisplayError(error));
    }
  }, []);

  useEffect(() => {
    void refreshDocuments();
    void refreshDashboard();
  }, [refreshDashboard, refreshDocuments]);

  useEffect(() => {
    if (selectedDocumentId) {
      void loadDocument(selectedDocumentId);
    }
  }, [loadDocument, selectedDocumentId]);

  const handleStatusChanged = useCallback(
    (event: DocumentStatusChangedEvent) => {
      setNotifications((current) => [event, ...current].slice(0, 6));
      setDocuments((current) =>
        current.map((document) =>
          document.document_id === event.document_id
            ? applyStatusEvent(document, event)
            : document,
        ),
      );
      setSelectedDocument((current) =>
        current?.document_id === event.document_id
          ? applyStatusEvent(current, event)
          : current,
      );

      if (selectedDocumentId === event.document_id) {
        void loadDocument(event.document_id);
      }

      void refreshDashboard();
    },
    [loadDocument, refreshDashboard, selectedDocumentId],
  );

  const socketState = useDocumentNotifications(handleStatusChanged);

  const statusCounts = useMemo(() => {
    if (dashboardSummary) {
      return dashboardSummary.by_status;
    }

    return DOCUMENT_STATUSES.reduce<Record<DocumentStatus, number>>(
      (accumulator, status) => {
        accumulator[status] = documents.filter(
          (document) => document.status === status,
        ).length;
        return accumulator;
      },
      {
        UPLOADED: 0,
        PROCESSING: 0,
        COMPLIANT: 0,
        NON_COMPLIANT: 0,
        FAILED: 0,
      },
    );
  }, [dashboardSummary, documents]);

  async function handleUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedFile) {
      setPageError("Selecciona un archivo antes de subirlo.");
      return;
    }

    setUploadState("loading");
    try {
      const uploaded = await uploadDocument({
        file: selectedFile,
        documentType,
      });
      setSelectedFile(null);
      setSelectedDocumentId(uploaded.document_id);
      setSelectedDocument(uploaded);
      setUploadState("success");
      setPageError(null);
      await refreshDocuments();
      await refreshDashboard();
    } catch (error) {
      setUploadState("error");
      setPageError(toDisplayError(error));
    }
  }

  async function handleProcess(documentId: string) {
    setProcessing(documentId, true);
    setDocuments((current) =>
      current.map((document) =>
        document.document_id === documentId
          ? { ...document, status: "PROCESSING" }
          : document,
      ),
    );

    try {
      const response = await processDocument(documentId);
      mergeDocument(response.document);
      setSelectedDocument((current) =>
        current?.document_id === documentId ? response.document : current,
      );
      await refreshDashboard();
    } catch (error) {
      const documentFromError = getDocumentFromApiError(error);
      if (documentFromError) {
        mergeDocument(documentFromError);
      }
      setPageError(toDisplayError(error));
    } finally {
      setProcessing(documentId, false);
      void refreshDocuments();
      if (selectedDocumentId === documentId) {
        void loadDocument(documentId);
      }
    }
  }

  async function handleDownload(documentId: string) {
    setDownloadState("loading");
    try {
      const response = await getDownloadUrl(documentId);
      setDownloadUrl(response.url);
      setDownloadState("success");
      setPageError(null);
    } catch (error) {
      setDownloadState("error");
      setPageError(toDisplayError(error));
    }
  }

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    setSelectedFile(event.target.files?.[0] ?? null);
  }

  function handleDropZoneDragOver(event: DragEvent<HTMLDivElement>) {
    if (!event.dataTransfer.types.includes("Files")) {
      return;
    }
    event.preventDefault();
    event.dataTransfer.dropEffect = "copy";
    if (!isDraggingFile) {
      setIsDraggingFile(true);
    }
  }

  function handleDropZoneDragLeave(event: DragEvent<HTMLDivElement>) {
    if (event.currentTarget.contains(event.relatedTarget as Node | null)) {
      return;
    }
    setIsDraggingFile(false);
  }

  function handleDropZoneDrop(event: DragEvent<HTMLDivElement>) {
    if (!event.dataTransfer.types.includes("Files")) {
      return;
    }
    event.preventDefault();
    setIsDraggingFile(false);
    const file = event.dataTransfer.files?.[0];
    if (file) {
      setSelectedFile(file);
      setPageError(null);
    }
  }

  function mergeDocument(nextDocument: RegulatoryDocument) {
    setDocuments((current) => {
      const exists = current.some(
        (document) => document.document_id === nextDocument.document_id,
      );
      if (!exists) {
        return [nextDocument, ...current];
      }

      return current.map((document) =>
        document.document_id === nextDocument.document_id ? nextDocument : document,
      );
    });
  }

  function setProcessing(documentId: string, isProcessing: boolean) {
    setProcessingIds((current) => {
      const next = new Set(current);
      if (isProcessing) {
        next.add(documentId);
      } else {
        next.delete(documentId);
      }
      return next;
    });
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Plataforma regulatoria</p>
          <h1>Documentos</h1>
        </div>
        <div className="topbar-actions">
          <SocketIndicator state={socketState} />
          <button
            className="icon-button"
            type="button"
            onClick={() => void refreshDocuments()}
          >
            <RefreshCw aria-hidden="true" size={18} />
            <span>Actualizar</span>
          </button>
        </div>
      </header>

      {pageError ? (
        <div className="alert" role="alert">
          {pageError}
        </div>
      ) : null}

      <section className="dashboard-band" aria-label="Resumen">
        <SummaryStrip
          totalDocuments={dashboardSummary?.total_documents ?? totalDocuments}
          statusCounts={statusCounts}
          loading={dashboardState === "loading"}
        />
        <StatusBarChart counts={statusCounts} />
        <TypeSummary summary={dashboardSummary} />
      </section>

      <section className="workspace-grid" aria-label="Operación de documentos">
        <div className="workspace-main">
          <UploadDocumentForm
            documentType={documentType}
            selectedFile={selectedFile}
            isDraggingFile={isDraggingFile}
            uploadState={uploadState}
            onDocumentTypeChange={setDocumentType}
            onFileChange={handleFileChange}
            onSubmit={handleUpload}
            onDragOver={handleDropZoneDragOver}
            onDragLeave={handleDropZoneDragLeave}
            onDrop={handleDropZoneDrop}
          />

          <section className="panel" aria-labelledby="documents-title">
            <div className="panel-header">
              <div>
                <h2 id="documents-title">Lista</h2>
                <p>
                  {totalDocuments} documento{totalDocuments === 1 ? "" : "s"}
                </p>
              </div>
            </div>
            <DocumentTable
              documents={documents}
              isLoading={listState === "loading"}
              processingIds={processingIds}
              selectedDocumentId={selectedDocumentId}
              onSelect={setSelectedDocumentId}
              onProcess={(documentId) => void handleProcess(documentId)}
            />
          </section>
        </div>

        <aside className="side-column">
          <DocumentDetail
            document={selectedDocument}
            state={detailState}
            downloadUrl={downloadUrl}
            downloadState={downloadState}
            isProcessing={
              selectedDocument ? processingIds.has(selectedDocument.document_id) : false
            }
            onProcess={(documentId) => void handleProcess(documentId)}
            onDownload={(documentId) => void handleDownload(documentId)}
          />

          <NotificationsPanel notifications={notifications} />
        </aside>
      </section>
    </main>
  );
}

function applyStatusEvent(
  document: RegulatoryDocument,
  event: DocumentStatusChangedEvent,
): RegulatoryDocument {
  return {
    ...document,
    status: event.status,
    updated_at: event.checked_at,
    processed_at: event.checked_at,
  };
}

function getDocumentFromApiError(error: unknown): RegulatoryDocument | null {
  if (!(error instanceof ApiError) || !isRecord(error.payload)) {
    return null;
  }

  const document = error.payload.document;
  if (!isRecord(document)) {
    return null;
  }

  return document as unknown as RegulatoryDocument;
}

export default App;
