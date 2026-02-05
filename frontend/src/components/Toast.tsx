"use client";

import { useEffect, useState, useCallback, createContext, useContext, ReactNode } from "react";

interface ToastMessage {
  id: number;
  type: "success" | "error" | "info";
  message: string;
}

interface ToastContextValue {
  toast: (type: ToastMessage["type"], message: string) => void;
}

const ToastContext = createContext<ToastContextValue>({ toast: () => {} });

export function useToast() {
  return useContext(ToastContext);
}

let nextId = 0;

export function ToastProvider({ children }: { children: ReactNode }) {
  const [messages, setMessages] = useState<ToastMessage[]>([]);

  const toast = useCallback((type: ToastMessage["type"], message: string) => {
    const id = nextId++;
    setMessages((prev) => [...prev, { id, type, message }]);
  }, []);

  const remove = useCallback((id: number) => {
    setMessages((prev) => prev.filter((m) => m.id !== id));
  }, []);

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
      <div className="fixed bottom-4 right-4 z-[100] flex flex-col gap-2">
        {messages.map((msg) => (
          <ToastItem key={msg.id} msg={msg} onRemove={remove} />
        ))}
      </div>
    </ToastContext.Provider>
  );
}

function ToastItem({
  msg,
  onRemove,
}: {
  msg: ToastMessage;
  onRemove: (id: number) => void;
}) {
  useEffect(() => {
    const timer = setTimeout(() => onRemove(msg.id), 3500);
    return () => clearTimeout(timer);
  }, [msg.id, onRemove]);

  const colors = {
    success: "border-green-500 bg-green-50 text-green-800 dark:bg-green-900/30 dark:text-green-300 dark:border-green-700",
    error: "border-red-500 bg-red-50 text-red-800 dark:bg-red-900/30 dark:text-red-300 dark:border-red-700",
    info: "border-blue-500 bg-blue-50 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300 dark:border-blue-700",
  };

  return (
    <div
      className={`animate-slide-in rounded-lg border-l-4 px-4 py-3 text-sm shadow-lg ${colors[msg.type]}`}
    >
      {msg.message}
    </div>
  );
}
