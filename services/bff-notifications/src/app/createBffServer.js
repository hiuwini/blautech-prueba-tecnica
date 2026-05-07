import { createServer } from "node:http";

import { loadConfig } from "../config/index.js";
import { createSocketServer } from "../sockets/notificationsNamespace.js";
import { createApp } from "./createApp.js";

export function createBffServer(options = {}) {
  const config = options.config ?? loadConfig();
  const app = createApp({
    config,
    dashboardSummaryProvider: options.dashboardSummaryProvider,
  });
  const httpServer = createServer(app);
  const { io, notificationsNamespace } = createSocketServer(httpServer, config);

  app.locals.notificationsNamespace = notificationsNamespace;

  return {
    app,
    config,
    httpServer,
    io,
    notificationsNamespace,
  };
}
