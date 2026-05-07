export function notFoundHandler(request, response) {
  response.status(404).json({
    error: "NOT_FOUND",
    message: "Route was not found",
    path: request.path,
  });
}
