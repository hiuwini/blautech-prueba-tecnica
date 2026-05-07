export function toDisplayError(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }

  return "Ocurrio un error inesperado.";
}

export function isRecord(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}
