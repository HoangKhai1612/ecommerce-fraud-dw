import React, { useEffect, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { apiJson, PredictionRecord } from "../api";

type Message = {
  id: string;
  role: "user" | "ai";
  content: string;
  source?: string;
  ai_available?: boolean;
  sources?: string[];
  sql_query?: string;
  results?: Record<string, any>[];
};

const SUGGESTED_QUESTIONS = [
  "Co bao nhieu giao dich gian lan?",
  "Thong ke ty le gian lan theo san pham",
  "Data Warehouse co nhung bang nao?",
  "Pipeline ETL hoat dong nhu the nao?",
  "Model XGBoost duoc huan luyen nhu the nao?",
  "He thong co nhung thanh phan nao?",
];

export default function AIDataAnalyst() {
  const [searchParams] = useSearchParams();
  const contextId = searchParams.get("prediction") || undefined;
  const [context, setContext] = useState<PredictionRecord | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (contextId) {
      (async () => {
        try {
          const data = await apiJson<PredictionRecord>(
            `/predictions/${contextId}`
          );
          setContext(data);
        } catch {
          // context optional
        }
      })();
    }
  }, [contextId]);

  const scrollBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollBottom();
  }, [messages]);

  const send = async (question: string) => {
    if (!question.trim() || sending) return;
    const userMsg: Message = { id: Date.now().toString(), role: "user", content: question };
    setMessages((msgs) => [...msgs, userMsg]);
    setInput("");
    setSending(true);
    setError(null);

    try {
      const body: Record<string, any> = { question };
      const path = contextId ? `/ai/chat?prediction_id=${contextId}` : "/ai/chat";
      const data = await apiJson<any>(path, {
        method: "POST",
        body: JSON.stringify(body),
      });

      const aiMsg: Message = {
        id: Date.now().toString() + "a",
        role: "ai",
        content: data.answer,
        source: data.source,
        ai_available: data.ai_available,
        sources: data.sources,
        sql_query: data.sql_query,
        results: data.results,
      };
      setMessages((msgs) => [...msgs, aiMsg]);
    } catch (e: any) {
      setError(e.message || "AI Data Analyst khong tra loi duoc");
      setMessages((msgs) => [
        ...msgs,
        {
          id: Date.now().toString() + "a",
          role: "ai",
          content: "AI Data Analyst khong the xu ly yeu cau cua ban luc nay. Xin thu lai sau.",
        },
      ]);
    } finally {
      setSending(false);
    }
  };

  const handleSubmit = (ev: React.FormEvent) => {
    ev.preventDefault();
    send(input);
  };

  return (
    <div className="page">
      <div className="page-header">
        <h2>AI Data Analyst</h2>
      </div>

      <div className="card">
        <p style={{ margin: 0, fontSize: 13, color: "#94a3b8" }}>
          Tro ly AI ho tro truy van, thong ke va phan tich du lieu gian lan
          thuong mai dien tu tu Data Warehouse. Hoi ve du lieu, kien truc he
          thong, hoac ket qua model.
        </p>
      </div>

      {context && (
        <div className="card">
          <h3>Nguon du doan (tham khao)</h3>
          <div className="detail-row">
            <span className="k">Prediction ID</span>
            <span>{context.prediction_id}</span>
          </div>
          <div className="detail-row">
            <span className="k">Xac suat</span>
            <span>{(context.fraud_probability * 100).toFixed(4)}%</span>
          </div>
          <div className="detail-row">
            <span className="k">Nhan</span>
            <span className={context.is_fraud_predicted === 1 ? "label-fraud" : "label-legit"}>
              {context.is_fraud_predicted === 1 ? "GIAN LUAN" : "HOP LE"}
            </span>
          </div>
        </div>
      )}

      {messages.length === 0 && (
        <div className="card">
          <h3>Cau hoi goi y</h3>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
            {SUGGESTED_QUESTIONS.map((q) => (
              <button
                key={q}
                className="btn btn-secondary"
                style={{ fontSize: 12 }}
                onClick={() => send(q)}
                disabled={sending}
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="card" style={{ flex: 1, display: "flex", flexDirection: "column" }}>
        <div
          style={{
            flex: 1,
            overflowY: "auto",
            border: "1px solid #334155",
            borderRadius: 6,
            padding: 12,
            marginBottom: 10,
            background: "#0b1121",
            minHeight: 200,
          }}
        >
          {messages.length === 0 && (
            <div className="empty">
              Dat cau hoi ve du lieu, kien truc he thong, hoac ket qua model.
              AI se truy van Data Warehouse va tai lieu du an de tra loi.
            </div>
          )}
          {messages.map((m) => (
            <div
              key={m.id}
              style={{
                marginBottom: 12,
                padding: 10,
                borderRadius: 6,
                background: m.role === "user" ? "#1e293b" : "#0f172a",
                border: m.role === "user" ? "1px solid #38bdf8" : "none",
              }}
            >
              <div style={{ fontSize: 11, color: "#94a3b8", marginBottom: 4 }}>
                {m.role === "user" ? "Ban" : "AI Data Analyst"}{m.source ? ` (${m.source})` : ""}
              </div>
              <div style={{ whiteSpace: "pre-wrap", lineHeight: 1.6 }}>
                {m.content}
              </div>
               {m.sources && m.sources.length > 0 && (
                <div style={{ fontSize: 11, color: "#64748b", marginTop: 6 }}>
                  Nguon: {m.sources.join(", ")}
                </div>
              )}
              {m.sql_query && (
                <div style={{ marginTop: 8 }}>
                  <div style={{ fontSize: 11, color: "#94a3b8", marginBottom: 2 }}>SQL da thuc thi:</div>
                  <pre style={{ fontSize: 11, background: "#0b1121", padding: 8, borderRadius: 4, overflowX: "auto", color: "#e2e8f0" }}>
                    {m.sql_query}
                  </pre>
                </div>
              )}
              {m.results && m.results.length > 0 && (
                <div style={{ marginTop: 8, overflowX: "auto" }}>
                  <table style={{ width: "100%", fontSize: 11, borderCollapse: "collapse" }}>
                    <thead>
                      <tr>
                        {Object.keys(m.results[0]).map((k) => (
                          <th key={k} style={{ textAlign: "left", padding: "4px 6px", borderBottom: "1px solid #334155", color: "#94a3b8" }}>
                            {k}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {m.results.map((row, i) => (
                        <tr key={i}>
                          {Object.keys(row).map((k) => (
                            <td key={k} style={{ padding: "4px 6px", borderBottom: "1px solid #1e293b" }}>
                              {String(row[k] ?? "")}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  <div style={{ fontSize: 10, color: "#64748b", marginTop: 4 }}>
                    {m.results.length} dong du lieu (toi da 100)
                  </div>
                </div>
              )}
              {m.results && m.results.length === 0 && m.sql_query && (
                <div style={{ fontSize: 11, color: "#fbbf24", marginTop: 6 }}>
                  Truy van tra ve khong co ket qua.
                </div>
              )}
              {!m.ai_available && m.role === "ai" && (
                <div style={{ fontSize: 11, color: "#f87171", marginTop: 6 }}>
                  (AI/Database khong kha dung - thong bao he thong)
                </div>
              )}
            </div>
          ))}
          <div ref={messagesEndRef} />
          {error && <div className="alert alert-error" style={{ marginTop: 8 }}>{error}</div>}
        </div>

        <form onSubmit={handleSubmit} className="form" style={{ gridTemplateColumns: "1fr auto", gap: 8 }}>
          <div className="field">
            <input
              value={input}
              onChange={(ev) => setInput(ev.target.value)}
              placeholder="Hoi ve du lieu, kien truc, hoac model..."
              disabled={sending}
            />
          </div>
          <div className="field">
            <button
              className="btn btn-primary"
              type="submit"
              disabled={sending || !input.trim()}
            >
              {sending ? "Dang gui..." : "Gui"}
            </button>
          </div>
        </form>
        <p style={{ fontSize: 12, color: "#94a3b8", margin: 0 }}>
          AI Data Analyst truy van Data Warehouse (read-only) va tai lieu du an.
          Khong thay the ket qua model XGBoost va khong duoc dung de ra quyet dinh.
        </p>
      </div>
    </div>
  );
}
