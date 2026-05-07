import { Bell } from "lucide-react";

import { StatusBadge } from "../../../shared/ui/StatusBadge";
import { formatDate } from "../../../shared/utils/format";
import { formatDocumentType } from "../../documents/model/statuses";
import type { DocumentStatusChangedEvent } from "../model/types";

export function NotificationsPanel({
  notifications,
}: {
  notifications: DocumentStatusChangedEvent[];
}) {
  return (
    <section
      className="panel notifications-panel"
      aria-labelledby="notifications-title"
    >
      <div className="panel-header">
        <h2 id="notifications-title">Notificaciones</h2>
        <Bell aria-hidden="true" size={18} />
      </div>
      {notifications.length === 0 ? (
        <div className="empty-state">Sin eventos</div>
      ) : (
        <ul>
          {notifications.map((notification) => (
            <li key={`${notification.document_id}-${notification.checked_at}`}>
              <StatusBadge status={notification.status} />
              <div>
                <strong>{formatDocumentType(notification.document_type)}</strong>
                <span>{formatDate(notification.checked_at)}</span>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
