import express from "express";

export function createHealthRouter(config) {
  const router = express.Router();

  router.get("/health", (_request, response) => {
    response.json({
      status: "ok",
      service: config.serviceName,
    });
  });

  return router;
}
