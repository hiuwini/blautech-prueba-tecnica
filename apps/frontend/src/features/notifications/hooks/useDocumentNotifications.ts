import { useEffect, useState } from "react";
import { io } from "socket.io-client";

import { getSocketUrl } from "../api/socketClient";
import type { DocumentStatusChangedEvent } from "../model/types";

export type SocketConnectionState = "connecting" | "connected" | "disconnected";

export function useDocumentNotifications(
  onStatusChanged: (event: DocumentStatusChangedEvent) => void,
): SocketConnectionState {
  const [connectionState, setConnectionState] =
    useState<SocketConnectionState>("connecting");

  useEffect(() => {
    const socket = io(getSocketUrl(), {
      transports: ["websocket", "polling"],
      withCredentials: true,
    });

    socket.on("connect", () => {
      setConnectionState("connected");
    });

    socket.on("disconnect", () => {
      setConnectionState("disconnected");
    });

    socket.on("connect_error", () => {
      setConnectionState("disconnected");
    });

    socket.on("document-status-changed", onStatusChanged);

    return () => {
      socket.off("document-status-changed", onStatusChanged);
      socket.close();
    };
  }, [onStatusChanged]);

  return connectionState;
}
