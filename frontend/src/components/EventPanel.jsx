import { useState } from "react";

const DEMO_MODE = import.meta.env.VITE_DEMO_MODE === "true";

export default function EventPanel({ onAnalyze, loading }) {
  const [prompt, setPrompt] = useState("");

  const READY_PROMPTS = [
    { 
      label: "BC Place Concert", 
      prompt: "Concert at BC Place in Vancouver causing traffic surge and network congestion in surrounding neighborhoods." 
    },
    { 
      label: "Toronto Winter Storm", 
      prompt: "Severe winter storm impacting cellular infrastructure across Downtown Toronto core." 
    },
    { 
      label: "Union Station Outages", 
      prompt: "Multiple cell tower outages detected near Union Station, Toronto during evening rush hour." 
    },
    { 
      label: "Rogers Centre Packet Loss", 
      prompt: "Packet loss spike affecting towers around Rogers Centre and Toronto waterfront." 
    },
    { 
      label: "Canada Place Event", 
      prompt: "Major public event near Canada Place causing localized service degradation in Downtown Vancouver." 
    },
  ];

  const handlePromptClick = (promptText) => {
    // Only populate the textarea, don't auto-run
    setPrompt(promptText);
  };

  const run = (p) => {
    if (!p.trim()) return;
    setPrompt(p);
    onAnalyze(p);
  };

  return (
    <div style={{ padding: 16 }}>
      <h2 style={{ marginTop: 0 }}>Event Panel</h2>

      <textarea
        style={{ 
          width: "100%", 
          height: 70, 
          marginBottom: 8, 
          padding: 8,
          backgroundColor: "rgba(255,255,255,0.06)",
          border: "1px solid rgba(255,255,255,0.15)",
          borderRadius: 8,
          color: "rgba(255,255,255,0.95)",
          fontFamily: "inherit",
          fontSize: 13,
          resize: "vertical",
        }}
        placeholder="Enter event prompt here..."
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
      />

      <button
        onClick={() => run(prompt)}
        disabled={loading || !prompt.trim()}
        style={{
          width: "100%",
          padding: 10,
          marginBottom: 12,
          backgroundColor: loading ? "#ccc" : "#1976d2",
          color: "white",
          border: "none",
          borderRadius: 8,
          cursor: loading ? "not-allowed" : "pointer",
          fontWeight: 700,
        }}
      >
        {loading ? "Analyzing..." : DEMO_MODE ? "Load Demo Analysis" : "Analyze Event"}
      </button>

      {DEMO_MODE && (
        <div style={{ fontSize: 12, opacity: 0.7, marginBottom: 12 }}>
          Demo mode — this loads a bundled sample scenario (no live backend).{" "}
          <a
            href="https://github.com/Deinick/TelusGuardAI"
            target="_blank"
            rel="noopener noreferrer"
            style={{ color: "inherit" }}
          >
            Clone the repo to run the live AI pipeline →
          </a>
        </div>
      )}

      <div style={{ marginTop: 6 }}>
        <div style={{ fontWeight: 800, marginBottom: 8, color: "rgba(255,255,255,0.92)" }}>Ready Event Prompts</div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr", gap: 8 }}>
          {READY_PROMPTS.map((x) => (
            <button
              key={x.label}
              onClick={() => handlePromptClick(x.prompt)}
              disabled={loading}
              style={{
                width: "100%",
                padding: 10,
                backgroundColor: "rgba(255,255,255,0.03)",
                border: "1px solid rgba(255,255,255,0.08)",
                borderRadius: 8,
                cursor: loading ? "not-allowed" : "pointer",
                textAlign: "left",
                color: "rgba(255,255,255,0.92)",
                transition: "background 0.2s",
              }}
              onMouseEnter={(e) => {
                if (!loading) {
                  e.currentTarget.style.backgroundColor = "rgba(255,255,255,0.06)";
                }
              }}
              onMouseLeave={(e) => {
                if (!loading) {
                  e.currentTarget.style.backgroundColor = "rgba(255,255,255,0.03)";
                }
              }}
            >
              <div style={{ fontWeight: 700, fontSize: 13, color: "rgba(255,255,255,0.95)" }}>{x.label}</div>
              <div style={{ fontSize: 12, opacity: 0.65, marginTop: 2, color: "rgba(255,255,255,0.7)" }}>{x.prompt}</div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}