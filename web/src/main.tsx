import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./index.css";

// ── Cleanup any service workers registered on this origin (e.g. Metabase) ──
// Metabase registers a service worker on localhost that can intercept our
// requests and redirect to /login.  Unregister all SWs on startup so our
// Vite dev server is fully in control.
if ("serviceWorker" in navigator) {
  navigator.serviceWorker.getRegistrations().then((registrations) => {
    for (const registration of registrations) {
      registration.unregister();
    }
  });
  // Also clear all caches to avoid stale SW responses
  if ("caches" in window) {
    caches.keys().then((keys) => {
      keys.forEach((key) => caches.delete(key));
    });
  }
}

// ── Guard: if somehow we land on /login, /signin, etc. → redirect to / ──
if (typeof window !== "undefined") {
  const path = window.location.pathname.toLowerCase();
  if (
    path === "/login" ||
    path === "/signin" ||
    path === "/auth" ||
    path === "/register" ||
    path.startsWith("/login/") ||
    path.startsWith("/auth/")
  ) {
    window.history.replaceState({}, "", "/");
  }
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);