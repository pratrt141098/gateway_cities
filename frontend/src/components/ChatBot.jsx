import { useState, useRef, useEffect } from "react";
import { fetchChat } from "../api/cities";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

const GREETING = "Ask anything about Massachusetts gateway cities.";
const EXAMPLES = [
  "What share of Boston residents are foreign-born?",
  "Compare Lowell and Worcester.",
  "Show the foreign-born trend in Worcester since 2010.",
];

function normalizeTimeSeries(rows = []) {
  return rows
    .map((r) => ({
      year: Number(r.year),
      value: r.value == null ? null : Number(r.value),
      metric: r.metric,
      city: r.city,
    }))
    .filter(
      (r) =>
        Number.isFinite(r.year) && r.value != null && !Number.isNaN(r.value),
    )
    .sort((a, b) => a.year - b.year);
}

/* ---- component ---- */
export default function ChatBot() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const send = async () => {
    const q = input.trim();
    if (!q || loading) return;
    setInput("");
    setMessages((m) => [...m, { role: "user", text: q }]);
    setLoading(true);
    try {
      const res = await fetchChat(q);
      const chart =
        res?.chart?.type === "time_series" && Array.isArray(res?.chart?.data)
          ? { ...res.chart, data: normalizeTimeSeries(res.chart.data) }
          : null;
      setMessages((m) => [
        ...m,
        {
          role: "bot",
          text: res?.answer || "Sorry, I couldn't answer that.",
          chart,
        },
      ]);
    } catch {
      setMessages((m) => [
        ...m,
        { role: "bot", text: "Sorry, something went wrong. Please try again." },
      ]);
    }
    setLoading(false);
  };

  return (
    <div style={styles.wrapper}>
      {/* Collapsed bar — always visible */}
      <button
        style={{
          ...styles.header,
          borderRadius: open ? "10px 10px 0 0" : "10px",
        }}
        onClick={() => setOpen((o) => !o)}
      >
        <span style={styles.headerIcon}>💬</span>
        <span style={styles.headerTitle}>ACS Assistant</span>
        <span style={styles.headerToggle}>{open ? "▼" : "▲"}</span>
        {!open && <span style={styles.closeX}>×</span>}
      </button>

      {/* Expanded panel */}
      {open && (
        <div style={styles.body}>
          <div style={styles.messages}>
            {messages.length === 0 && (
              <div style={styles.welcome}>
                <p>{GREETING}</p>
                <p style={styles.examples}>
                  {EXAMPLES.map((ex, i) => (
                    <span key={i}>
                      <em>e.g. "{ex}"</em>
                      {i < EXAMPLES.length - 1 ? " or " : ""}
                    </span>
                  ))}
                </p>
              </div>
            )}
            {messages.map((m, i) => (
              <div
                key={i}
                style={{
                  ...styles.msg,
                  alignSelf: m.role === "user" ? "flex-end" : "flex-start",
                  background: m.role === "user" ? "#1a2540" : "#1e1f2e",
                  borderColor: m.role === "user" ? "#4e9af1" : "#2a2a3a",
                }}
              >
                {m.text.split("\n").map((line, li) => (
                  <span key={li}>
                    {line.startsWith("**") && line.endsWith("**") ? (
                      <strong>{line.slice(2, -2)}</strong>
                    ) : (
                      line
                    )}
                    {li < m.text.split("\n").length - 1 && <br />}
                  </span>
                ))}

                {m.role === "bot" && m.chart?.type === "time_series" && (
                  <div style={styles.chartWrap}>
                    <div style={styles.chartTitle}>{m.chart.title}</div>
                    <div style={styles.chartBox}>
                      <ResponsiveContainer width="100%" height={160}>
                        <LineChart data={m.chart.data}>
                          <XAxis dataKey="year" stroke="#9aa4b2" />
                          <YAxis stroke="#9aa4b2" />
                          <Tooltip
                            contentStyle={{
                              background: "#13141f",
                              border: "1px solid #2a2a3a",
                              borderRadius: 8,
                              color: "#e0e0e0",
                            }}
                          />
                          <Line
                            type="monotone"
                            dataKey="value"
                            stroke="#4e9af1"
                            strokeWidth={2}
                            dot={false}
                          />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                )}
              </div>
            ))}
            {loading && (
              <div
                style={{
                  ...styles.msg,
                  background: "#1e1f2e",
                  borderColor: "#2a2a3a",
                  alignSelf: "flex-start",
                }}
              >
                <em style={{ color: "#888" }}>Thinking…</em>
              </div>
            )}
            <div ref={endRef} />
          </div>

          <form
            style={styles.inputRow}
            onSubmit={(e) => {
              e.preventDefault();
              send();
            }}
          >
            <input
              style={styles.input}
              placeholder="Ask a question…"
              value={input}
              onChange={(e) => setInput(e.target.value)}
            />
            <button type="submit" style={styles.sendBtn} disabled={loading}>
              ▶
            </button>
          </form>
        </div>
      )}
    </div>
  );
}

/* ---- inline styles ---- */
const styles = {
  wrapper: {
    position: "fixed",
    bottom: 24,
    right: 24,
    width: 340,
    zIndex: 9999,
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
    display: "flex",
    flexDirection: "column",
  },
  header: {
    display: "flex",
    alignItems: "center",
    gap: 8,
    padding: "10px 14px",
    background: "#1a1b2e",
    border: "1px solid #2a2a3a",
    color: "#ccc",
    fontSize: "0.85rem",
    fontWeight: 600,
    cursor: "pointer",
    userSelect: "none",
  },
  headerIcon: { fontSize: "1rem" },
  headerTitle: { flex: 1, textAlign: "left", color: "#e0e0e0" },
  headerToggle: { fontSize: "0.65rem", color: "#888" },
  closeX: { fontSize: "1rem", color: "#888", marginLeft: 4 },
  body: {
    display: "flex",
    flexDirection: "column",
    background: "#13141f",
    border: "1px solid #2a2a3a",
    borderTop: "none",
    borderRadius: "0 0 10px 10px",
    height: 360,
  },
  messages: {
    flex: 1,
    overflowY: "auto",
    padding: "12px",
    display: "flex",
    flexDirection: "column",
    gap: 8,
  },
  welcome: {
    color: "#999",
    fontSize: "0.82rem",
    textAlign: "center",
    marginTop: 40,
    lineHeight: 1.6,
  },
  examples: {
    marginTop: 12,
    color: "#6e7a94",
    fontSize: "0.78rem",
  },
  msg: {
    maxWidth: "88%",
    padding: "8px 12px",
    borderRadius: 8,
    border: "1px solid",
    fontSize: "0.82rem",
    color: "#ddd",
    lineHeight: 1.5,
    whiteSpace: "pre-wrap",
    wordBreak: "break-word",
  },
  chartWrap: {
    marginTop: 10,
  },
  chartTitle: {
    fontSize: "0.78rem",
    color: "#9aa4b2",
    marginBottom: 6,
  },
  chartBox: {
    width: "100%",
    height: 170,
    background: "#13141f",
    border: "1px solid #2a2a3a",
    borderRadius: 10,
    padding: 8,
  },
  inputRow: {
    display: "flex",
    gap: 6,
    padding: "8px 10px",
    borderTop: "1px solid #2a2a3a",
  },
  input: {
    flex: 1,
    padding: "8px 10px",
    borderRadius: 8,
    border: "1px solid #2a2a3a",
    background: "#1e1f2e",
    color: "#e0e0e0",
    fontSize: "0.82rem",
    outline: "none",
  },
  sendBtn: {
    padding: "6px 12px",
    borderRadius: 8,
    border: "1px solid #4e9af1",
    background: "#4e9af1",
    color: "#fff",
    fontSize: "0.85rem",
    cursor: "pointer",
  },
};
