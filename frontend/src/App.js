import React, { useEffect, useRef, useState } from "react";
import axios from "axios";
import WineGrid from "./components/WineGrid";

/* Small in-file bubble component so you don't need extra files */
function ChatBubble({ who = "bot", text = "" }) {
  const isUser = who === "user";
  return (
    <div className="msg-row" style={{ justifyContent: isUser ? "flex-end" : "flex-start" }}>
      <div className={`msg-bubble ${isUser ? "msg-user" : "msg-bot"}`}>
        <div>{text}</div>
        <div className="msg-meta">{isUser ? "You" : "Sommelier"}</div>
      </div>
    </div>
  );
}

export default function App() {
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState([]); // {who:'user'|'bot', text}
  const [quickAnswer, setQuickAnswer] = useState("");
  const [wines, setWines] = useState([]);
  const [loadingQuick, setLoadingQuick] = useState(false);
  const [loadingDetailed, setLoadingDetailed] = useState(false);
  const [error, setError] = useState("");

  const endRef = useRef(null);

  // Resizable sidebar
  const [sidebarWidth, setSidebarWidth] = useState(360);
  const draggingRef = useRef(false);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, wines]);

  useEffect(() => {
    const onMouseMove = (e) => {
      if (!draggingRef.current) return;
      const min = 240;
      const max = Math.max(340, window.innerWidth - 320);
      const newW = Math.min(Math.max(min, window.innerWidth - e.clientX), max);
      setSidebarWidth(newW);
    };
    const onMouseUp = () => {
      draggingRef.current = false;
      document.body.style.cursor = "";
    };
    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("mouseup", onMouseUp);
    return () => {
      window.removeEventListener("mousemove", onMouseMove);
      window.removeEventListener("mouseup", onMouseUp);
    };
  }, []);

  const startDrag = (e) => {
    draggingRef.current = true;
    document.body.style.cursor = "col-resize";
    e.preventDefault();
  };

  const pushMsg = (who, text) => setMessages((p) => [...p, { who, text }]);

  const askQuick = async () => {
    if (!query.trim()) return;
    setError("");
    setLoadingQuick(true);
    setWines([]);
    pushMsg("user", query);
    pushMsg("bot", "Thinking…");

    try {
      const res = await axios.post(
        "http://localhost:5000/ask_quick",
        { query },
        { timeout: 60000 }
      );
      const ans = res.data.answer || "(no quick answer)";
      setMessages((prev) => {
        const out = [...prev];
        for (let i = out.length - 1; i >= 0; i--) {
          if (out[i].who === "bot" && out[i].text === "Thinking…") {
            out[i] = { who: "bot", text: ans };
            return out;
          }
        }
        return [...out, { who: "bot", text: ans }];
      });
      setQuickAnswer(ans);
      setQuery("");
    } catch (e) {
      const msg = e.response?.data?.error || e.message || "Error fetching quick answer";
      setError(msg);
      pushMsg("bot", "Oops: " + msg);
    } finally {
      setLoadingQuick(false);
    }
  };

  const askDetailed = async () => {
    if (!quickAnswer) return;
    setError("");
    setLoadingDetailed(true);
    pushMsg("bot", "Looking up best matches from our cellar…");

    try {
      const res = await axios.post(
        "http://localhost:5000/ask_detailed",
        { query: quickAnswer, quick_answer: quickAnswer },
        { timeout: 120000 }
      );
      const ans = res.data.answer || "(no detailed answer)";
      const matched = res.data.structured_wines || [];
      pushMsg("bot", ans);
      setWines(matched);
    } catch (e) {
      const msg = e.response?.data?.error || e.message || "Error fetching details";
      setError(msg);
      pushMsg("bot", "Oops: " + msg);
    } finally {
      setLoadingDetailed(false);
    }
  };

  const onKey = (e) => {
    if (e.key === "Enter") askQuick();
  };

  return (
    <div className="app-fullscreen">
      {/* Header */}
      <div className="chat-header">
        <div>
          <div style={{ fontWeight: 700 }}>🍇 Wine Chatbot</div>
          <div style={{ fontSize: 13, opacity: 0.9 }}>
            Fast DeepSeek answers with optional dataset-backed review
          </div>
        </div>
        <div style={{ fontSize: 13 }}>
          Connected cellar: <strong>8470 wines</strong>
        </div>
      </div>

      {/* Body */}
      <div className="chat-body">
        {/* Left: chat */}
        <div className="chat-panel">
          <div className="chat-window" aria-live="polite">
            {messages.length === 0 ? (
              <div style={{ color: "#6b7280", marginTop: 8 }}>
                Hi 🍷 — Ask for a wine or try: “Italian reds under 100 SEK”
              </div>
            ) : (
              messages.map((m, i) => (
                <ChatBubble key={i} who={m.who} text={m.text} />
              ))
            )}
            <div ref={endRef} />
          </div>

          <div className="chat-input-bar">
            <input
              className="form-control"
              placeholder="Ask: e.g. 'Portuguese whites near me'"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={onKey}
              disabled={loadingDetailed}
            />
            <button
              className="btn btn-outline-primary"
              onClick={askQuick}
              disabled={loadingQuick || loadingDetailed || !query.trim()}
            >
              {loadingQuick ? <span className="spinner-dot" /> : "Quick"}
            </button>
            <button
              className="btn btn-primary"
              onClick={askDetailed}
              disabled={loadingDetailed || !quickAnswer}
            >
              {loadingDetailed ? <span className="spinner-dot" /> : "Detailed"}
            </button>
          </div>
        </div>

        {/* Right: resizable sidebar */}
        <div
          className="sidebar"
          style={{ width: sidebarWidth }}
        >
          <div className="sidebar-handle" onMouseDown={startDrag} />
          <div className="sidebar-scroll">
            <div className="mb-2">
              <h6 className="mb-1">Tips</h6>
              <div className="text-muted small">
                Try: <em>Italian reds under 100 SEK</em> · <em>Food pairing for Pinot Noir</em>
              </div>
            </div>

            <WineGrid wines={wines} />

            <div className="text-muted small mt-2">
              API: <code>/ask_quick</code> • <code>/ask_detailed</code>
            </div>
            {error ? <div className="alert alert-danger mt-2">{error}</div> : null}
          </div>
        </div>
      </div>
    </div>
  );
}
