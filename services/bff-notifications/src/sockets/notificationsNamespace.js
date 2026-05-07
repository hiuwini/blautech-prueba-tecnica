import { Server } from "socket.io";

export function createSocketServer(httpServer, config) {
  const io = new Server(httpServer, {
    cors: {
      origin: config.corsAllowedOrigins,
      methods: ["GET", "POST"],
      credentials: true,
    },
  });
  const notificationsNamespace = io.of(config.socketNamespace);

  notificationsNamespace.on("connection", (socket) => {
    socket.data.connected_at = new Date().toISOString();
  });

  return { io, notificationsNamespace };
}
