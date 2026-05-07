export class ApiError extends Error {
  readonly status: number;
  readonly payload: unknown;

  constructor(message: string, status: number, payload: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.payload = payload;
  }
}

export async function requestJson<T>(
  input: URL,
  init: RequestInit = {},
): Promise<T> {
  const response = await fetch(input, init);
  const payload = await parseJson(response);

  if (!response.ok) {
    throw new ApiError(
      resolveErrorMessage(payload, response.status),
      response.status,
      payload,
    );
  }

  return payload as T;
}

export function apiUrl(baseUrl: string, pathname: string): URL {
  return new URL(pathname, baseUrl);
}

async function parseJson(response: Response): Promise<unknown> {
  const text = await response.text();
  if (!text) {
    return null;
  }

  try {
    return JSON.parse(text) as unknown;
  } catch {
    return text;
  }
}

function resolveErrorMessage(payload: unknown, status: number): string {
  if (isRecord(payload) && typeof payload.message === "string") {
    return payload.message;
  }

  return `HTTP ${status}`;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}
