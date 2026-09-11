import type { SystemNotification } from "../types/notification";

export interface NotificationService {
  list(): readonly SystemNotification[];
  getUnreadCount(): number;
  markAsRead(id: string): void;
  markAllAsRead(): void;
  clearAll(): void;
  addNotification(notification: Omit<SystemNotification, "id" | "timestamp" | "read">): void;
  subscribe(listener: () => void): () => void;
}

let notifications: SystemNotification[] = [
  {
    id: "notif-1",
    type: "agent",
    title: "Agent Execution Completed",
    message: 'Research Agent finished analyzing "Employee Handbook 2026".',
    timestamp: "2 minutes ago",
    read: false,
    link: "/agents",
  },
  {
    id: "notif-2",
    type: "workflow",
    title: "Workflow Run Succeeded",
    message: 'Workflow "Employee Data Sync" completed 14 steps successfully.',
    timestamp: "18 minutes ago",
    read: false,
    link: "/workflows",
  },
  {
    id: "notif-3",
    type: "knowledge",
    title: "Document Ingested",
    message: '"Remote Work Policy" is now RAG-ready for Assistant querying.',
    timestamp: "1 hour ago",
    read: true,
    link: "/knowledge",
  },
  {
    id: "notif-4",
    type: "system",
    title: "Security Audit Clear",
    message: "Automated security scanning passed with 0 vulnerabilities detected.",
    timestamp: "3 hours ago",
    read: true,
  },
];

const listeners = new Set<() => void>();

function notify() {
  listeners.forEach((listener) => listener());
}

export const notificationService: NotificationService = {
  list: () => notifications,
  getUnreadCount: () => notifications.filter((n) => !n.read).length,
  markAsRead: (id: string) => {
    notifications = notifications.map((n) => (n.id === id ? { ...n, read: true } : n));
    notify();
  },
  markAllAsRead: () => {
    notifications = notifications.map((n) => ({ ...n, read: true }));
    notify();
  },
  clearAll: () => {
    notifications = [];
    notify();
  },
  addNotification: (item) => {
    const newNotif: SystemNotification = {
      ...item,
      id: `notif-${Date.now()}`,
      timestamp: "Just now",
      read: false,
    };
    notifications = [newNotif, ...notifications];
    notify();
  },
  subscribe: (listener: () => void) => {
    listeners.add(listener);
    return () => listeners.delete(listener);
  },
};
