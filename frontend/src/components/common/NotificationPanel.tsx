import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { AlertCircle, Bot, CheckCheck, Database, Trash2, Workflow, X } from "lucide-react";
import { notificationService } from "../../services/notificationService";
import type { SystemNotification } from "../../types/notification";

type NotificationPanelProps = {
  isOpen: boolean;
  onClose: () => void;
};

function NotificationPanel({ isOpen, onClose }: NotificationPanelProps) {
  const [notifications, setNotifications] = useState<readonly SystemNotification[]>(() =>
    notificationService.list()
  );
  const panelRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  useEffect(() => {
    return notificationService.subscribe(() => {
      setNotifications(notificationService.list());
    });
  }, []);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (panelRef.current && !panelRef.current.contains(e.target as Node)) {
        onClose();
      }
    };
    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const handleNotificationClick = (notif: SystemNotification) => {
    notificationService.markAsRead(notif.id);
    if (notif.link) {
      navigate(notif.link);
      onClose();
    }
  };

  const getNotificationIcon = (type: SystemNotification["type"]) => {
    switch (type) {
      case "agent":
        return <Bot size={15} />;
      case "workflow":
        return <Workflow size={15} />;
      case "knowledge":
        return <Database size={15} />;
      default:
        return <AlertCircle size={15} />;
    }
  };

  return (
    <div className="notification-panel" ref={panelRef} aria-label="Notifications Panel">
      <div className="notification-panel-header">
        <div>
          <h3>Notifications</h3>
          <span>{notifications.filter((n) => !n.read).length} unread</span>
        </div>

        <div className="notification-panel-actions">
          <button
            className="panel-text-action"
            type="button"
            onClick={() => notificationService.markAllAsRead()}
            title="Mark all as read"
          >
            <CheckCheck size={14} />
            <span>Mark all read</span>
          </button>
          <button
            className="panel-icon-action"
            type="button"
            onClick={() => notificationService.clearAll()}
            title="Clear all notifications"
          >
            <Trash2 size={14} />
          </button>
          <button className="panel-icon-action" type="button" onClick={onClose} title="Close panel">
            <X size={14} />
          </button>
        </div>
      </div>

      <div className="notification-panel-list">
        {notifications.length > 0 ? (
          notifications.map((n) => (
            <div
              key={n.id}
              className={`notification-item ${!n.read ? "unread" : ""}`}
              onClick={() => handleNotificationClick(n)}
              role="button"
              tabIndex={0}
            >
              <div className={`notification-icon-wrapper type-${n.type}`}>
                {getNotificationIcon(n.type)}
              </div>
              <div className="notification-info">
                <div className="notification-title-row">
                  <strong>{n.title}</strong>
                  <span className="notification-time">{n.timestamp}</span>
                </div>
                <p>{n.message}</p>
              </div>
            </div>
          ))
        ) : (
          <div className="notification-empty">
            <p>No notifications.</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default NotificationPanel;
