import { loadFrontendConfig } from "../../../config/env";
import { apiUrl, requestJson } from "../../../shared/api/http";
import type {
  DocumentListResponse,
  DownloadUrlResponse,
  ProcessDocumentResponse,
  RegulatoryDocument,
} from "../model/types";

export interface UploadDocumentInput {
  file: File;
  documentType: string;
}

const config = loadFrontendConfig();

export async function listDocuments(
  limit = 50,
  offset = 0,
): Promise<DocumentListResponse> {
  const url = apiUrl(config.documentProcessingBaseUrl, "/api/v1/documents");
  url.searchParams.set("limit", String(limit));
  url.searchParams.set("offset", String(offset));

  return requestJson<DocumentListResponse>(url, {
    headers: {
      Accept: "application/json",
    },
  });
}

export async function getDocument(documentId: string): Promise<RegulatoryDocument> {
  return requestJson<RegulatoryDocument>(
    apiUrl(config.documentProcessingBaseUrl, `/api/v1/documents/${documentId}`),
    {
      headers: {
        Accept: "application/json",
      },
    },
  );
}

export async function uploadDocument(
  input: UploadDocumentInput,
): Promise<RegulatoryDocument> {
  const formData = new FormData();
  formData.append("file", input.file);
  formData.append("document_type", input.documentType);

  return requestJson<RegulatoryDocument>(
    apiUrl(config.documentProcessingBaseUrl, "/api/v1/documents/upload"),
    {
      method: "POST",
      body: formData,
      headers: {
        Accept: "application/json",
      },
    },
  );
}

export async function processDocument(
  documentId: string,
): Promise<ProcessDocumentResponse> {
  return requestJson<ProcessDocumentResponse>(
    apiUrl(
      config.documentProcessingBaseUrl,
      `/api/v1/documents/${documentId}/process`,
    ),
    {
      method: "POST",
      headers: {
        Accept: "application/json",
      },
    },
  );
}

export async function getDownloadUrl(
  documentId: string,
): Promise<DownloadUrlResponse> {
  return requestJson<DownloadUrlResponse>(
    apiUrl(
      config.documentProcessingBaseUrl,
      `/api/v1/documents/${documentId}/download-url`,
    ),
    {
      headers: {
        Accept: "application/json",
      },
    },
  );
}
