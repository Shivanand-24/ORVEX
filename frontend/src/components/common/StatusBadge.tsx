type StatusBadgeProps = {
  status: string;
  type?: "agent" | "workflow" | "knowledge" | "generic";
};

function StatusBadge({ status, type = "generic" }: StatusBadgeProps) {
  const normalized = status.toLowerCase();

  let variant = "active";
  if (["paused", "draft", "notindexed"].includes(normalized)) {
    variant = "paused";
  } else if (["processing", "indexing", "pending"].includes(normalized)) {
    variant = "processing";
  } else if (["failed", "indexfailed", "offline"].includes(normalized)) {
    variant = "failed";
  }

  return (
    <span className={`status-badge status-badge-${variant} type-${type}`}>
      <span className="status-badge-dot"></span>
      {status}
    </span>
  );
}

export default StatusBadge;
