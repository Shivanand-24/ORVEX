export type ToastType = "success" | "error" | "info" | "warning";

export type ToastMessage = {
  id: string;
  type: ToastType;
  title: string;
  description?: string;
};

export interface ToastService {
  list(): readonly ToastMessage[];
  show(title: string, description?: string, type?: ToastType): void;
  dismiss(id: string): void;
  subscribe(listener: () => void): () => void;
}

let toasts: ToastMessage[] = [];
const listeners = new Set<() => void>();

function notify() {
  listeners.forEach((listener) => listener());
}

export const toastService: ToastService = {
  list: () => toasts,
  show: (title, description, type = "success") => {
    const id = `toast-${Date.now()}`;
    const newToast: ToastMessage = { id, title, description, type };
    toasts = [...toasts, newToast];
    notify();

    setTimeout(() => {
      toasts = toasts.filter((t) => t.id !== id);
      notify();
    }, 4000);
  },
  dismiss: (id: string) => {
    toasts = toasts.filter((t) => t.id !== id);
    notify();
  },
  subscribe: (listener: () => void) => {
    listeners.add(listener);
    return () => listeners.delete(listener);
  },
};
