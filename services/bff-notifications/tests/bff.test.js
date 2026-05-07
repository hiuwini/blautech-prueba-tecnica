import assert from "node:assert/strict";
import { once } from "node:events";
import test from "node:test";

import { io as createSocketClient } from "socket.io-client";

import { buildDashboardSummary, createBffServer } from "../src/index.js";

const VALID_WEBHOOK_PAYLOAD = {
  document_id: "11111111-1111-4111-8111-111111111111",
  status: "COMPLIANT",
  document_type: "financial_report",
  checked_at: "2026-05-05T10:30:00Z",
};

test("GET /health returns service status", async (t) => {
  const runtime = await startBff();
  t.after(() => closeBff(runtime));

  const response = await fetch(`${runtime.baseUrl}/health`);

  assert.equal(response.status, 200);
  assert.deepEqual(await response.json(), {
    status: "ok",
    service: "bff-notifications",
  });
});

test("POST /api/v1/webhooks/processing-complete emits document-status-changed", async (t) => {
  const runtime = await startBff();
  t.after(() => closeBff(runtime));

  const client = createSocketClient(`${runtime.baseUrl}/notifications`, {
    transports: ["websocket"],
    reconnection: false,
    timeout: 1000,
  });
  t.after(() => client.close());

  await withTimeout(once(client, "connect"));
  const eventPromise = withTimeout(
    once(client, "document-status-changed").then(([payload]) => payload),
  );

  const response = await fetch(
    `${runtime.baseUrl}/api/v1/webhooks/processing-complete`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        ...VALID_WEBHOOK_PAYLOAD,
        check_id: "22222222-2222-4222-8222-222222222222",
        details: "Document is compliant",
      }),
    },
  );

  assert.equal(response.status, 202);
  assert.deepEqual(await response.json(), {
    status: "accepted",
    event: "document-status-changed",
    document_id: VALID_WEBHOOK_PAYLOAD.document_id,
  });
  assert.deepEqual(await eventPromise, VALID_WEBHOOK_PAYLOAD);
});

test("POST /api/v1/webhooks/processing-complete emits FAILED status changes", async (t) => {
  const runtime = await startBff();
  t.after(() => closeBff(runtime));
  const failedPayload = {
    ...VALID_WEBHOOK_PAYLOAD,
    status: "FAILED",
    checked_at: "2026-05-05T10:45:00Z",
  };

  const client = createSocketClient(`${runtime.baseUrl}/notifications`, {
    transports: ["websocket"],
    reconnection: false,
    timeout: 1000,
  });
  t.after(() => client.close());

  await withTimeout(once(client, "connect"));
  const eventPromise = withTimeout(
    once(client, "document-status-changed").then(([payload]) => payload),
  );

  const response = await fetch(
    `${runtime.baseUrl}/api/v1/webhooks/processing-complete`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        ...failedPayload,
        details: "SOAP Gateway is unavailable",
      }),
    },
  );

  assert.equal(response.status, 202);
  assert.deepEqual(await eventPromise, failedPayload);
});

test("POST /api/v1/webhooks/processing-complete rejects invalid payload", async (t) => {
  const runtime = await startBff();
  t.after(() => closeBff(runtime));

  const response = await fetch(
    `${runtime.baseUrl}/api/v1/webhooks/processing-complete`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        document_id: "not-a-uuid",
        status: "PROCESSING",
        document_type: "",
        checked_at: "2026-05-05 10:30:00",
      }),
    },
  );
  const body = await response.json();

  assert.equal(response.status, 400);
  assert.equal(body.error, "INVALID_REQUEST");
  assert.match(body.details.join("\n"), /document_id must be a valid UUID/);
  assert.match(body.details.join("\n"), /status must be one of/);
  assert.match(body.details.join("\n"), /document_type is required/);
  assert.match(body.details.join("\n"), /checked_at must be an ISO 8601 UTC timestamp/);
});

test("GET /api/v1/dashboard/summary returns aggregated contract", async (t) => {
  const summary = {
    total_documents: 2,
    aggregated_documents: 2,
    is_complete: true,
    by_status: {
      UPLOADED: 1,
      PROCESSING: 0,
      COMPLIANT: 1,
      NON_COMPLIANT: 0,
      FAILED: 0,
    },
    by_document_type: {
      financial_report: 2,
    },
    recent_documents: [],
    source: "document-processing",
  };
  const runtime = await startBff({
    dashboardSummaryProvider: async () => summary,
  });
  t.after(() => closeBff(runtime));

  const response = await fetch(`${runtime.baseUrl}/api/v1/dashboard/summary`);

  assert.equal(response.status, 200);
  assert.deepEqual(await response.json(), summary);
});

test("buildDashboardSummary aggregates FastAPI document list payload", () => {
  const summary = buildDashboardSummary({
    total: 2,
    items: [
      {
        document_id: "11111111-1111-4111-8111-111111111111",
        document_type: "financial_report",
        original_filename: "report.pdf",
        status: "UPLOADED",
        updated_at: "2026-05-05T10:00:00Z",
        processed_at: null,
      },
      {
        document_id: "22222222-2222-4222-8222-222222222222",
        document_type: "financial_report",
        original_filename: "report-2.pdf",
        status: "COMPLIANT",
        updated_at: "2026-05-05T10:30:00Z",
        processed_at: "2026-05-05T10:30:00Z",
      },
    ],
  });

  assert.equal(summary.total_documents, 2);
  assert.equal(summary.aggregated_documents, 2);
  assert.equal(summary.by_status.UPLOADED, 1);
  assert.equal(summary.by_status.COMPLIANT, 1);
  assert.deepEqual(summary.by_document_type, {
    financial_report: 2,
  });
  assert.equal(summary.recent_documents.length, 2);
});

async function startBff(options = {}) {
  const runtime = createBffServer({
    config: testConfig(),
    dashboardSummaryProvider: options.dashboardSummaryProvider,
  });

  await new Promise((resolve, reject) => {
    runtime.httpServer.once("error", reject);
    runtime.httpServer.listen(0, "127.0.0.1", resolve);
  });

  const address = runtime.httpServer.address();

  return {
    ...runtime,
    baseUrl: `http://127.0.0.1:${address.port}`,
  };
}

async function closeBff(runtime) {
  await new Promise((resolve) => runtime.io.close(resolve));

  if (runtime.httpServer.listening) {
    await new Promise((resolve, reject) => {
      runtime.httpServer.close((error) => {
        if (error) {
          reject(error);
          return;
        }
        resolve();
      });
    });
  }
}

function testConfig() {
  return {
    host: "127.0.0.1",
    port: 0,
    serviceName: "bff-notifications",
    frontendBaseUrl: "http://localhost:3000",
    corsAllowedOrigins: ["http://localhost:3000"],
    socketNamespace: "/notifications",
    fastapiBaseUrl: "http://document-processing:8000",
    fastapiTimeoutMs: 1000,
    dashboardPageSize: 100,
    dashboardMaxDocuments: 500,
  };
}

function withTimeout(promise, milliseconds = 1500) {
  let timeout;
  const timeoutPromise = new Promise((_, reject) => {
    timeout = setTimeout(() => {
      reject(new Error(`Timed out after ${milliseconds}ms`));
    }, milliseconds);
  });

  return Promise.race([promise, timeoutPromise]).finally(() => {
    clearTimeout(timeout);
  });
}
