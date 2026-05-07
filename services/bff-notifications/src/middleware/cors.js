export function createCorsMiddleware(allowedOrigins) {
  const allowed = new Set(allowedOrigins);

  return (request, response, next) => {
    const origin = request.headers.origin;

    if (origin && allowed.has(origin)) {
      response.setHeader("Access-Control-Allow-Origin", origin);
      response.setHeader("Vary", "Origin");
      response.setHeader("Access-Control-Allow-Credentials", "true");
      response.setHeader("Access-Control-Allow-Methods", "GET,POST,OPTIONS");
      response.setHeader("Access-Control-Allow-Headers", "Content-Type,Accept");
    }

    if (request.method === "OPTIONS") {
      if (origin && !allowed.has(origin)) {
        response.status(403).json({
          error: "CORS_ORIGIN_NOT_ALLOWED",
          message: "Origin is not allowed",
        });
        return;
      }

      response.status(204).end();
      return;
    }

    if (origin && !allowed.has(origin)) {
      response.status(403).json({
        error: "CORS_ORIGIN_NOT_ALLOWED",
        message: "Origin is not allowed",
      });
      return;
    }

    next();
  };
}
