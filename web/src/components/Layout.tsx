import { ReactNode, useState } from "react";
import { NavLink, useLocation } from "react-router-dom";

const ITEMS: { to: string; label: string }[] = [
  { to: "/", label: "Tong quan" },
  { to: "/dw", label: "Data Warehouse" },
  { to: "/transactions", label: "Giao dich" },
  { to: "/ml", label: "Machine Learning" },
  { to: "/models", label: "So sanh mo hinh" },
  { to: "/batch", label: "Du doan hang loat" },
  { to: "/history", label: "Lich su du doan" },
  { to: "/ai", label: "AI Assistant" },
  { to: "/monitoring", label: "Giam sat he thong" },
  { to: "/status", label: "Trang thai he thong" },
  { to: "/settings", label: "Cau hinh" },
];

export default function Layout({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false);
  const location = useLocation();

  return (
    <div className="app">
      <button className="mobile-menu" onClick={() => setOpen((o) => !o)}>
        Menu
      </button>
      <aside className={`sidebar ${open ? "open" : ""}`}>
        <div className="sidebar-brand">
          <span className="dot" />
          Fraud Detection
        </div>
        <nav>
          {ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                isActive ? "active" : ""
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-footer">
          Phase 31 - Unified Web Application
        </div>
      </aside>
      <div className="main">
        <div className="topbar">
          <h1>{currentPage(location.pathname)}</h1>
          <div className="topbar-right">
            <a href="/docs" target="_blank" rel="noopener noreferrer">
              API docs
            </a>
          </div>
        </div>
        <div className="content"><div className="page">{children}</div></div>
      </div>
    </div>
  );
}

function currentPage(path: string) {
  const map: Record<string, string> = {
    "/": "Tong quan",
    "/dw": "Data Warehouse",
    "/transactions": "Giao dich",
    "/testing": "Kiem thu giao dich",
    "/history": "Lich su du doan",
    "/ml": "Machine Learning",
    "/models": "So sanh mo hinh",
    "/batch": "Du doan hang loat",
    "/ai": "AI Assistant",
    "/monitoring": "Giam sat he thong",
    "/status": "Trang thai he thong",
    "/settings": "Cau hinh",
  };
  return map[path] || "He thong";
}
