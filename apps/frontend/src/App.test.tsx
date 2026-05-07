import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import App from "./app/App";
import type { RegulatoryDocument } from "./features/documents/model/types";
import type { DocumentStatusChangedEvent } from "./features/notifications/model/types";

const { closeSocket, socketHandlers } = vi.hoisted(() => ({
  closeSocket: vi.fn(),
  socketHandlers: new Map<string, (payload?: unknown) => void>(),
}));

vi.mock("socket.io-client", () => ({
  io: vi.fn(() => ({
    on: vi.fn((eventName: string, handler: (payload?: unknown) => void) => {
      socketHandlers.set(eventName, handler);
    }),
    off: vi.fn(),
    close: closeSocket,
  })),
}));

const baseDocument: RegulatoryDocument = {
  document_id: "2d9a8f73-cc77-4df2-b370-7a908863fb2d",
  user_id: null,
  document_type: "financial_report",
  original_filename: "balance.pdf",
  content_type: "application/pdf",
  size_bytes: 2048,
  bucket_name: "regulatory-documents",
  object_key: "documents/2d9a8f73-cc77-4df2-b370-7a908863fb2d/balance.pdf",
  status: "UPLOADED",
  created_at: "2026-05-06T12:00:00Z",
  updated_at: "2026-05-06T12:00:00Z",
  processed_at: null,
  latest_compliance_check: null,
};

describe("App", () => {
  beforeEach(() => {
    socketHandlers.clear();
    closeSocket.mockClear();
    vi.stubGlobal("fetch", vi.fn(mockFetch));
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("renders dashboard summary and documents from backend contracts", async () => {
    render(<App />);

    expect(await screen.findByText("balance.pdf")).toBeInTheDocument();
    expect(screen.getByText("1 documento")).toBeInTheDocument();
    expect(screen.getAllByText("Cargado").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Financial Report").length).toBeGreaterThan(0);
  });

  it("uploads a document with selected document_type", async () => {
    const fetchMock = vi.mocked(fetch);
    render(<App />);

    await screen.findByText("balance.pdf");

    const file = new File(["content"], "tax.pdf", { type: "application/pdf" });
    fireEvent.change(screen.getByLabelText("Tipo"), {
      target: { value: "tax_filing" },
    });
    fireEvent.change(screen.getByLabelText("Archivo"), {
      target: { files: [file] },
    });
    fireEvent.click(screen.getByRole("button", { name: "Subir" }));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        expect.objectContaining({
          pathname: "/api/v1/documents/upload",
        }),
        expect.objectContaining({
          method: "POST",
          body: expect.any(FormData),
        }),
      );
    });
  });

  it("loads document detail and requests a download URL", async () => {
    const fetchMock = vi.mocked(fetch);
    render(<App />);

    await screen.findByText("balance.pdf");
    fireEvent.click(
      screen.getByRole("button", { name: "Ver detalle de balance.pdf" }),
    );

    expect(await screen.findByText(baseDocument.document_id)).toBeInTheDocument();
    expect(screen.getByText(baseDocument.object_key)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Descarga" }));

    const downloadLink = await screen.findByRole("link", {
      name: "Abrir enlace de descarga",
    });
    expect(downloadLink).toHaveAttribute(
      "href",
      "http://minio.local/regulatory-documents/balance.pdf?expires=900",
    );
    expect(fetchMock).toHaveBeenCalledWith(
      expect.objectContaining({
        pathname: `/api/v1/documents/${baseDocument.document_id}/download-url`,
      }),
      expect.objectContaining({
        headers: {
          Accept: "application/json",
        },
      }),
    );
  });

  it("accepts a file dropped on the upload drop-zone and uploads it", async () => {
    const fetchMock = vi.mocked(fetch);
    render(<App />);

    await screen.findByText("balance.pdf");

    const dropZone = screen.getByTestId("upload-dropzone");
    const droppedFile = new File(["payload"], "dropped.pdf", { type: "application/pdf" });
    const dataTransfer = buildDataTransfer([droppedFile]);

    fireEvent.dragEnter(dropZone, { dataTransfer });
    expect(dropZone.className).toContain("drop-zone-active");
    fireEvent.drop(dropZone, { dataTransfer });
    expect(dropZone.className).not.toContain("drop-zone-active");

    expect(screen.getByText("Listo para subir: dropped.pdf")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Subir" }));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        expect.objectContaining({ pathname: "/api/v1/documents/upload" }),
        expect.objectContaining({ method: "POST", body: expect.any(FormData) }),
      );
    });
  });

  it("renders a status bar chart with one bar per document status", async () => {
    render(<App />);

    await screen.findByText("balance.pdf");

    const chart = screen.getByTestId("status-chart");
    expect(chart).toHaveAttribute("aria-label", expect.stringContaining("total"));

    for (const status of ["uploaded", "processing", "compliant", "non_compliant", "failed"]) {
      expect(screen.getByTestId(`status-chart-bar-${status}`)).toBeInTheDocument();
    }

    const uploadedRect = screen
      .getByTestId("status-chart-bar-uploaded")
      .querySelector("rect");
    expect(uploadedRect).not.toBeNull();
    expect(Number(uploadedRect!.getAttribute("height"))).toBeGreaterThan(0);
  });

  it("updates visual status when Socket.IO emits document-status-changed", async () => {
    render(<App />);

    expect(await screen.findByText("balance.pdf")).toBeInTheDocument();

    const event: DocumentStatusChangedEvent = {
      document_id: baseDocument.document_id,
      document_type: "financial_report",
      status: "COMPLIANT",
      checked_at: "2026-05-06T12:05:00Z",
    };

    act(() => {
      socketHandlers.get("document-status-changed")?.(event);
    });

    expect(await screen.findByText("Notificaciones")).toBeInTheDocument();
    expect(screen.getAllByText("Cumple").length).toBeGreaterThan(0);
  });
});

async function mockFetch(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  const url = new URL(input instanceof URL ? input.href : String(input));
  const method = init?.method ?? "GET";

  if (url.pathname === "/api/v1/dashboard/summary") {
    return jsonResponse({
      total_documents: 1,
      aggregated_documents: 1,
      is_complete: true,
      by_status: {
        UPLOADED: 1,
        PROCESSING: 0,
        COMPLIANT: 0,
        NON_COMPLIANT: 0,
        FAILED: 0,
      },
      by_document_type: {
        financial_report: 1,
      },
      recent_documents: [],
      source: "document-processing",
    });
  }

  if (url.pathname === "/api/v1/documents" && method === "GET") {
    return jsonResponse({
      items: [baseDocument],
      total: 1,
      limit: 50,
      offset: 0,
    });
  }

  if (url.pathname === "/api/v1/documents/upload" && method === "POST") {
    return jsonResponse(
      {
        ...baseDocument,
        document_id: "64b6f2ff-2e0a-4d46-8f2c-3ee73d56ce8d",
        document_type: "tax_filing",
        original_filename: "tax.pdf",
      },
      201,
    );
  }

  if (url.pathname === `/api/v1/documents/${baseDocument.document_id}`) {
    return jsonResponse(baseDocument);
  }

  if (url.pathname === `/api/v1/documents/${baseDocument.document_id}/download-url`) {
    return jsonResponse({
      document_id: baseDocument.document_id,
      url: "http://minio.local/regulatory-documents/balance.pdf?expires=900",
      expires_in_seconds: 900,
    });
  }

  return jsonResponse({ message: "Not found" }, 404);
}

function jsonResponse(payload: unknown, status = 200): Response {
  return new Response(JSON.stringify(payload), {
    status,
    headers: {
      "Content-Type": "application/json",
    },
  });
}

function buildDataTransfer(files: File[]): DataTransfer {
  const fileList = {
    length: files.length,
    item: (index: number) => files[index] ?? null,
    [Symbol.iterator]: function* () {
      for (const file of files) yield file;
    },
  } as unknown as FileList;
  files.forEach((file, index) => {
    Object.defineProperty(fileList, index, { value: file, enumerable: true });
  });

  return {
    files: fileList,
    items: [] as unknown as DataTransferItemList,
    types: ["Files"],
    dropEffect: "copy",
    effectAllowed: "all",
    clearData: () => undefined,
    getData: () => "",
    setData: () => undefined,
    setDragImage: () => undefined,
  } as unknown as DataTransfer;
}
