import { useEffect, useState } from "react";
import { AlertCircle, CheckCircle2, Info, X } from "lucide-react";
import { toastService, type ToastMessage } from "../../services/toastService";

function Toast() {
  const [toasts, setToasts] = useState<readonly ToastMessage[]>(() =>
    toastService.list()
  );

  useEffect(() => {
    return toastService.subscribe(() => {
      setToasts(toastService.list());
    });
  }, []);

  if (toasts.length === 0) return null;

  return (
    <div className="toast-container" aria-live="polite">
      {toasts.map((toast) => {
        return (
          <div key={toast.id} className={`toast toast-${toast.type}`}>
            <div className="toast-icon">
              {toast.type === "success" && <CheckCircle2 size={18} />}
              {toast.type === "error" && <AlertCircle size={18} />}
              {(toast.type === "info" || toast.type === "warning") && <Info size={18} />}
            </div>

            <div className="toast-body">
              <strong>{toast.title}</strong>
              {toast.description && <span>{toast.description}</span>}
            </div>

            <button
              className="toast-close"
              type="button"
              onClick={() => toastService.dismiss(toast.id)}
              aria-label="Dismiss toast"
            >
              <X size={14} />
            </button>
          </div>
        );
      })}
    </div>
  );
}

export default Toast;
