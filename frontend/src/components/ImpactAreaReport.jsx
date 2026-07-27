import { useState } from "react";

function getSeverityColor(severity) {
  const s = (severity || "").toLowerCase();
  if (s === "critical") return "#ef4444";
  if (s === "high") return "#f59e0b";
  if (s === "moderate") return "#fbc02d";
  if (s === "low") return "#22c55e";
  return "#22c55e";
}

function getSeverityLabel(severity) {
  const s = (severity || "").toLowerCase();
  return s.charAt(0).toUpperCase() + s.slice(1);
}

function getSeverityGlow(severity) {
  const s = (severity || "").toLowerCase();
  if (s === "critical") return "0 0 12px rgba(239,68,68,0.4), 0 0 6px rgba(239,68,68,0.3)";
  if (s === "high") return "0 0 12px rgba(245,158,11,0.4), 0 0 6px rgba(245,158,11,0.3)";
  if (s === "moderate") return "0 0 12px rgba(251,192,45,0.4), 0 0 6px rgba(251,192,45,0.3)";
  if (s === "low") return "0 0 12px rgba(34,197,94,0.4), 0 0 6px rgba(34,197,94,0.3)";
  return "0 0 12px rgba(34,197,94,0.4), 0 0 6px rgba(34,197,94,0.3)";
}

function getMitigationColor(action) {
  const lower = (action || "").toLowerCase();
  if (lower.includes("load-balance") || lower.includes("reroute") || lower.includes("shift") || lower.includes("traffic")) {
    return "rgba(37,99,235,0.95)"; // blue
  }
  if (lower.includes("capacity") || lower.includes("allocate") || lower.includes("reserve")) {
    return "rgba(168,85,247,0.92)"; // purple
  }
  if (lower.includes("maintenance") || lower.includes("dispatch") || lower.includes("repair")) {
    return "rgba(255,255,255,0.06)"; // dark grey
  }
  return "rgba(59,130,246,0.85)"; // default blue
}

function getMitigationIcon(action) {
  const lower = (action || "").toLowerCase();
  if (lower.includes("load-balance") || lower.includes("reroute") || lower.includes("shift")) {
    return "⚡";
  }
  if (lower.includes("capacity") || lower.includes("allocate") || lower.includes("reserve")) {
    return "📊";
  }
  if (lower.includes("maintenance") || lower.includes("dispatch") || lower.includes("repair")) {
    return "🔧";
  }
  return "⚙️";
}

function MetricCard({ title, value, valueColor, valueFontSize = 20 }) {
  return (
    <div
      style={{
        background: "linear-gradient(135deg, rgba(255,255,255,0.03) 0%, rgba(255,255,255,0.06) 100%)",
        border: "1px solid rgba(255,255,255,0.12)",
        borderRadius: 12,
        padding: 12,
        boxShadow: "0 2px 8px rgba(0,0,0,0.15)",
      }}
    >
      <div style={{ fontSize: 12, color: "rgba(255,255,255,0.65)" }}>
        {title}
      </div>
      <div style={{ display: "flex", justifyContent: "space-between", marginTop: 8 }}>
        <div style={{ fontSize: valueFontSize, fontWeight: 800, color: valueColor || "rgba(255,255,255,0.95)" }}>
          {value}
        </div>
      </div>
    </div>
  );
}

function ActionButton({ icon, label, color }) {
  return (
    <button
      style={{
        width: "100%",
        display: "flex",
        alignItems: "center",
        gap: 10,
        padding: "10px 12px",
        borderRadius: 12,
        border: "1px solid rgba(255,255,255,0.08)",
        background: color,
        color: "rgba(255,255,255,0.95)",
        fontWeight: 800,
        cursor: "pointer",
        transition: "all 0.2s",
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.opacity = "0.9";
        e.currentTarget.style.transform = "translateY(-1px)";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.opacity = "1";
        e.currentTarget.style.transform = "translateY(0)";
      }}
    >
      <span style={{ fontSize: 16 }}>{icon}</span>
      <span style={{ flex: 1, textAlign: "left" }}>{label}</span>
    </button>
  );
}

export default function ImpactAreaReport({ area }) {
  const [showFullReasoning, setShowFullReasoning] = useState(false);

  if (!area) return null;

  const severityColor = getSeverityColor(area.severity);
  const severityLabel = getSeverityLabel(area.severity);
  const severityGlow = getSeverityGlow(area.severity);
  const severityScore = Math.round((area.severityScore || 0) * 100);
  const confidence = area.confidence != null
    ? typeof area.confidence === "number"
      ? `${Math.round(area.confidence * 100)}%`
      : String(area.confidence)
    : null;
  
  // Tint colors for metric values based on severity
  const tintedWhite = severityColor; // Use severity color for tinted numbers

  // Format estimated impact to show as "~X users" with tilde
  const formatEstimatedImpact = (impact) => {
    if (!impact || impact === "—") return "—";
    const impactStr = String(impact);
    // Check if it already has "users" or starts with ~
    const lowerImpact = impactStr.toLowerCase();
    if (lowerImpact.includes("user")) {
      // Already has users, ensure it starts with ~ if it's a number
      const numMatch = impactStr.match(/[\d,]+/);
      if (numMatch && !impactStr.startsWith("~")) {
        return `~${impactStr}`;
      }
      return impactStr;
    }
    // Extract number and add ~ and "users"
    const numMatch = impactStr.match(/[\d,]+/);
    if (numMatch) {
      return `~${numMatch[0]} users`;
    }
    return `~${impactStr} users`;
  };

  // Format mitigation actions
  const mitigationActions = Array.isArray(area.mitigation)
    ? area.mitigation
    : typeof area.mitigation === "string"
    ? [area.mitigation]
    : area.mitigation
    ? [String(area.mitigation)]
    : [];

  // Check if this is a BC Place event (hide Area Actions for demo)
  const isBCPlaceEvent = area.eventName?.toLowerCase().includes("bc place") || 
                         area.id?.toLowerCase().includes("bc_place") ||
                         area.id?.toLowerCase().includes("event_bc_place");

  // Truncate reasoning if long
  const reasoning = area.reasoning || "";
  const shouldTruncate = reasoning.length > 150;
  const displayReasoning = shouldTruncate && !showFullReasoning
    ? reasoning.substring(0, 150) + "..."
    : reasoning;

  return (
    <div>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
        <div style={{ fontSize: 16, fontWeight: 900, flex: 1 }}>
          {area.name}
        </div>
        <div
          style={{
            padding: "6px 10px",
            borderRadius: 999,
            border: `1px solid ${severityColor}40`,
            background: `linear-gradient(135deg, ${severityColor}20 0%, ${severityColor}10 100%)`,
            fontSize: 12,
            color: severityColor,
            fontWeight: 900,
            textTransform: "capitalize",
            marginLeft: 12,
            boxShadow: severityGlow,
          }}
        >
          {severityLabel}
        </div>
      </div>

      {confidence && (
        <div style={{ fontSize: 12, color: "rgba(255,255,255,0.65)", marginBottom: 12 }}>
          Confidence: <span style={{ fontWeight: 700, color: "rgba(255,255,255,0.9)" }}>{confidence}</span>
        </div>
      )}

      {/* Severity Bar */}
      <div style={{ marginTop: 12, marginBottom: 14 }}>
        <div style={{ fontSize: 12, color: "rgba(255,255,255,0.65)", marginBottom: 6 }}>
          Severity Score
        </div>
        <div
          style={{
            height: 10,
            borderRadius: 999,
            background: "rgba(255,255,255,0.08)",
            overflow: "hidden",
            border: "1px solid rgba(255,255,255,0.08)",
          }}
        >
          <div
            style={{
              width: `${severityScore}%`,
              height: "100%",
              background: severityColor,
              boxShadow: `0 0 8px ${severityColor}80, 0 0 4px ${severityColor}60`,
              transition: "width 0.3s ease",
            }}
          />
        </div>
        <div style={{ textAlign: "right", fontSize: 12, color: "rgba(255,255,255,0.75)", marginTop: 6 }}>
          {severityScore}%
        </div>
      </div>

      {/* Key Metrics Cards */}
      <div style={{ marginTop: 14 }}>
        <div style={{ fontSize: 13, fontWeight: 900, marginBottom: 10 }}>
          Impact Metrics
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
          <MetricCard
            title="Towers Affected"
            value={area.towerCount ?? 0}
            valueColor={tintedWhite}
            severityColor={severityColor}
          />
          <MetricCard
            title="Estimated Impact"
            value={formatEstimatedImpact(area.estimated_impact)}
            valueColor={tintedWhite}
            severityColor={severityColor}
          />
          <MetricCard
            title="Severity Score"
            value={`${severityScore}%`}
            valueColor={severityColor}
            severityColor={severityColor}
          />
          <MetricCard
            title="Event"
            value={area.eventName || "—"}
            valueFontSize={14}
          />
        </div>
      </div>

      {/* AI Explanation */}
      {reasoning && (
        <div style={{ marginTop: 14 }}>
          <div style={{ fontSize: 13, fontWeight: 900, marginBottom: 10 }}>
            AI Explanation
          </div>
          <div
            style={{
              background: "rgba(255,255,255,0.03)",
              border: "1px solid rgba(255,255,255,0.08)",
              borderRadius: 12,
              padding: 12,
              boxShadow: "inset 0 1px 3px rgba(0,0,0,0.2)",
            }}
          >
            <div style={{ fontSize: 13, color: "rgba(255,255,255,0.85)", lineHeight: 1.8, whiteSpace: "pre-wrap" }}>
              {displayReasoning}
            </div>
            {shouldTruncate && (
              <button
                onClick={() => setShowFullReasoning(!showFullReasoning)}
                style={{
                  marginTop: 8,
                  padding: "6px 12px",
                  borderRadius: 6,
                  border: "1px solid rgba(255,255,255,0.08)",
                  background: "rgba(255,255,255,0.05)",
                  color: "rgba(255,255,255,0.9)",
                  fontSize: 12,
                  fontWeight: 600,
                  cursor: "pointer",
                  transition: "all 0.2s",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = "rgba(255,255,255,0.1)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = "rgba(255,255,255,0.05)";
                }}
              >
                {showFullReasoning ? "Show less" : "Show more"}
              </button>
            )}
          </div>
        </div>
      )}

      {!reasoning && (
        <div style={{ marginTop: 14 }}>
          <div style={{ fontSize: 13, fontWeight: 900, marginBottom: 10 }}>
            AI Explanation
          </div>
          <div
            style={{
              background: "rgba(255,255,255,0.03)",
              border: "1px solid rgba(255,255,255,0.08)",
              borderRadius: 12,
              padding: 12,
              boxShadow: "inset 0 1px 3px rgba(0,0,0,0.2)",
            }}
          >
            <div style={{ fontSize: 13, color: "rgba(255,255,255,0.5)", fontStyle: "italic", lineHeight: 1.8 }}>
              No explanation provided.
            </div>
          </div>
        </div>
      )}

      {/* Area Actions - Hidden for BC Place events (demo) */}
      {!isBCPlaceEvent && mitigationActions.length > 0 && (
        <div style={{ marginTop: 14 }}>
          <div style={{ fontSize: 13, fontWeight: 900, marginBottom: 10 }}>
            Area Actions
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {mitigationActions.map((action, index) => (
              <ActionButton
                key={index}
                icon={getMitigationIcon(action)}
                label={action}
                color={getMitigationColor(action)}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
