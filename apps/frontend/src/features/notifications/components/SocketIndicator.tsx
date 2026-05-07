import { Wifi, WifiOff } from "lucide-react";

import type { SocketConnectionState } from "../hooks/useDocumentNotifications";

export function SocketIndicator({ state }: { state: SocketConnectionState }) {
  const isConnected = state === "connected";
  return (
    <div className={`socket-indicator ${isConnected ? "online" : "offline"}`}>
      {isConnected ? (
        <Wifi aria-hidden="true" size={16} />
      ) : (
        <WifiOff aria-hidden="true" size={16} />
      )}
      <span>
        {isConnected
          ? "Socket activo"
          : state === "connecting"
            ? "Conectando"
            : "Socket inactivo"}
      </span>
    </div>
  );
}
