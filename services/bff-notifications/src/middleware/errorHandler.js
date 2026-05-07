export function errorHandler(error, _request, response, next) {
  if (response.headersSent) {
    next(error);
    return;
  }

  if (error instanceof SyntaxError && "body" in error) {
    response.status(400).json({
      error: "INVALID_REQUEST",
      message: "JSON body is invalid",
    });
    return;
  }

  response.status(500).json({
    error: "INTERNAL_SERVER_ERROR",
    message: "Unexpected BFF error",
  });
}
