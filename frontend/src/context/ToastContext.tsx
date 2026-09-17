import React, { createContext, useContext, useState, useCallback } from 'react';
import { AlertCircle, CheckCircle2, Info, AlertTriangle, X } from 'lucide-react';

export type ToastType = 'error' | 'success' | 'warning' | 'info';

export interface Toast {
  id: string;
  message: string;
  type: ToastType;
  duration?: number;
}

interface ToastContextType {
  showToast: (message: string, type?: ToastType, duration?: number) => void;
  removeToast: (id: string) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const showToast = useCallback(
    (message: string, type: ToastType = 'info', duration: number = 4500) => {
      const id = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
      const newToast: Toast = { id, message, type, duration };

      setToasts((prev) => [...prev, newToast]);

      if (duration > 0) {
        setTimeout(() => {
          removeToast(id);
        }, duration);
      }
    },
    [removeToast]
  );

  const getIcon = (type: ToastType) => {
    switch (type) {
      case 'error':
        return <AlertCircle className="w-5 h-5 text-rose-400 flex-shrink-0 mt-0.5" />;
      case 'success':
        return <CheckCircle2 className="w-5 h-5 text-emerald-400 flex-shrink-0 mt-0.5" />;
      case 'warning':
        return <AlertTriangle className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />;
      case 'info':
      default:
        return <Info className="w-5 h-5 text-sky-400 flex-shrink-0 mt-0.5" />;
    }
  };

  const getStyles = (type: ToastType) => {
    switch (type) {
      case 'error':
        return 'bg-stone-900/95 border-rose-500/40 text-stone-100 shadow-rose-950/30';
      case 'success':
        return 'bg-stone-900/95 border-emerald-500/40 text-stone-100 shadow-emerald-950/30';
      case 'warning':
        return 'bg-stone-900/95 border-amber-500/40 text-stone-100 shadow-amber-950/30';
      case 'info':
      default:
        return 'bg-stone-900/95 border-amber-400/30 text-stone-100 shadow-stone-950/40';
    }
  };

  return (
    <ToastContext.Provider value={{ showToast, removeToast }}>
      {children}
      {/* Toast floating notifications container */}
      <div
        className="fixed bottom-5 right-5 z-50 flex flex-col gap-2.5 max-w-sm w-full pointer-events-none px-4 sm:px-0"
        aria-live="assertive"
      >
        {toasts.map((toast) => (
          <div
            key={toast.id}
            role="alert"
            className={`pointer-events-auto border rounded-xl p-3.5 shadow-xl backdrop-blur-md transition-all duration-300 transform flex items-start gap-3 text-sm ${getStyles(
              toast.type
            )} animate-in fade-in slide-in-from-bottom-3`}
          >
            {getIcon(toast.type)}
            <div className="flex-1 font-sans text-stone-200 pr-1 leading-snug">
              {toast.message}
            </div>
            <button
              type="button"
              onClick={() => removeToast(toast.id)}
              className="text-stone-400 hover:text-stone-200 transition-colors p-0.5 rounded focus:outline-none"
              aria-label="Fechar notificação"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
};

export const useToast = (): ToastContextType => {
  const context = useContext(ToastContext);
  if (!context) {
    // Graceful fallback if invoked outside ToastProvider
    return {
      showToast: (msg: string) => console.log(`[Toast Fallback]: ${msg}`),
      removeToast: () => {},
    };
  }
  return context;
};
