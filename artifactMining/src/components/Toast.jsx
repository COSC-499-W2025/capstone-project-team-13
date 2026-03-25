import React, { useState, useEffect } from "react";
import "./Toast.css";

// Module-level event bus — import { toast } from "./Toast" from anywhere
const _listeners = [];

export function toast(msg, type = "ok", duration = 3200) {
  _listeners.forEach(fn => fn({ msg, type, duration }));
}

export default function Toast() {
  const [items, setItems] = useState([]);

  useEffect(() => {
    function handle({ msg, type, duration }) {
      const id = Date.now() + Math.random();
      setItems(prev => [...prev, { id, msg, type }]);
      setTimeout(() => setItems(prev => prev.filter(t => t.id !== id)), duration);
    }
    _listeners.push(handle);
    return () => {
      const i = _listeners.indexOf(handle);
      if (i > -1) _listeners.splice(i, 1);
    };
  }, []);

  return (
    <div className="toast-container" aria-live="polite">
      {items.map(t => (
        <div key={t.id} className={`toast-item toast-${t.type}`}>
          <span className="toast-icon">{t.type === "ok" ? "✓" : t.type === "warn" ? "⚠" : "✕"}</span>
          {t.msg}
        </div>
      ))}
    </div>
  );
}
