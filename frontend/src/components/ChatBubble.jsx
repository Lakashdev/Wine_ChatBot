import React from "react";

export default function ChatBubble({ who = "bot", text = "" }) {
  const isUser = who === "user";
  const align = isUser ? "justify-content-end" : "justify-content-start";
  const bubbleClass = isUser ? "bg-gradient-user" : "bg-white";
  const bubbleStyle = isUser ? {
    background: "linear-gradient(135deg,#ffd6e0 0%, #ffefef 100%)",
  } : {
    background: "linear-gradient(135deg,#ffffff 0%, #f1f5f9 100%)"
  };

  return (
    <div className={`d-flex mb-3 ${align}`}>
      <div className="p-3 rounded shadow-sm" style={{ maxWidth: "78%", ...bubbleStyle }}>
        <div style={{ whiteSpace: "pre-wrap" }}>{text}</div>
        <div className="text-muted small mt-2">{isUser ? "You" : "Sommelier"}</div>
      </div>
    </div>
  );
}
