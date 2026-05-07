import { fetchDocumentsPage, UpstreamDashboardError } from "../clients/documentProcessingClient.js";
import { DOCUMENT_STATUSES } from "../contracts/statuses.js";

export { UpstreamDashboardError };

export async function fetchDashboardSummary(config, fetchImpl = globalThis.fetch) {
  const allItems = [];
  let total = 0;
  let offset = 0;
  const pageSize = Math.min(config.dashboardPageSize, 100);

  do {
    const remainingDocuments = config.dashboardMaxDocuments - allItems.length;
    if (remainingDocuments <= 0) {
      break;
    }

    const page = await fetchDocumentsPage(config, fetchImpl, {
      limit: Math.min(pageSize, remainingDocuments),
      offset,
    });

    total = page.total;
    allItems.push(...page.items);
    offset += page.items.length;

    if (page.items.length === 0) {
      break;
    }
  } while (offset < total && allItems.length < config.dashboardMaxDocuments);

  return buildDashboardSummary({
    items: allItems,
    total,
    aggregated_documents: allItems.length,
    is_complete: allItems.length >= total,
  });
}

export function buildDashboardSummary(payload) {
  if (!isPlainObject(payload) || !Array.isArray(payload.items)) {
    throw new UpstreamDashboardError("Document Processing returned invalid JSON");
  }

  const total = Number.isInteger(payload.total) ? payload.total : payload.items.length;
  const byStatus = Object.fromEntries(
    DOCUMENT_STATUSES.map((status) => [status, 0]),
  );
  const byDocumentType = {};

  for (const item of payload.items) {
    if (!isPlainObject(item)) {
      continue;
    }

    if (typeof item.status === "string" && item.status.trim()) {
      byStatus[item.status] = (byStatus[item.status] ?? 0) + 1;
    }

    if (
      typeof item.document_type === "string" &&
      item.document_type.trim()
    ) {
      byDocumentType[item.document_type] =
        (byDocumentType[item.document_type] ?? 0) + 1;
    }
  }

  return {
    total_documents: total,
    aggregated_documents:
      Number.isInteger(payload.aggregated_documents)
        ? payload.aggregated_documents
        : payload.items.length,
    is_complete:
      typeof payload.is_complete === "boolean"
        ? payload.is_complete
        : payload.items.length >= total,
    by_status: byStatus,
    by_document_type: byDocumentType,
    recent_documents: payload.items.slice(0, 5).map(toRecentDocument),
    source: "document-processing",
  };
}

function toRecentDocument(item) {
  return {
    document_id: item.document_id ?? null,
    document_type: item.document_type ?? null,
    original_filename: item.original_filename ?? null,
    status: item.status ?? null,
    updated_at: item.updated_at ?? null,
    processed_at: item.processed_at ?? null,
  };
}

function isPlainObject(value) {
  return (
    value !== null &&
    typeof value === "object" &&
    !Array.isArray(value)
  );
}
