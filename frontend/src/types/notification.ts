export type NotificationType = "agent" | "workflow" | "knowledge" | "system";

export type SystemNotification = {
  id: string;
  type: NotificationType;
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
  link?: string;
};
