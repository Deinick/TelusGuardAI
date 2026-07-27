function StatusRow({ label, value, color }) {
  return (
    <div
      style={{
        display: "flex",
        justifyContent: "space-between",
        fontSize: 13,
        marginBottom: 6,
      }}
    >
      <span style={{ color: "rgba(255,255,255,0.65)" }}>{label}</span>
      <span style={{ fontWeight: 900, color }}>{value}</span>
    </div>
  );
}

// Generate consistent simulated values based on tower/area ID
function generateSystemMetrics(id) {
  if (!id) {
    return {
      actionReadiness: 0.85,
      affectedRadius: 2.5,
      automationMode: "Monitoring",
      rollbackAvailable: true,
      lastAIDecision: "No actions taken",
    };
  }

  // Generate deterministic but unique values based on ID hash
  let hash = 0;
  for (let i = 0; i < id.length; i++) {
    hash = ((hash << 5) - hash) + id.charCodeAt(i);
    hash = hash & hash;
  }
  const absHash = Math.abs(hash);

  // Action Readiness: 70-95% based on hash
  const actionReadiness = 0.70 + (absHash % 26) / 100;

  // Affected Radius: 0.5-5.0 km based on hash
  const affectedRadius = 0.5 + ((absHash % 46) / 10);

  // Automation Mode: rotate through options based on hash
  const modes = ["Monitoring", "Active", "Paused"];
  const automationMode = modes[absHash % 3];

  // Rollback Available: 80% chance based on hash
  const rollbackAvailable = (absHash % 10) < 8;

  // Last AI Decision: various options based on hash
  const decisions = [
    "Load balancing optimized",
    "Capacity allocated",
    "Frequency adjusted",
    "No actions taken",
    "Maintenance scheduled",
    "Traffic rerouted",
  ];
  const lastAIDecision = decisions[absHash % decisions.length];

  return {
    actionReadiness,
    affectedRadius,
    automationMode,
    rollbackAvailable,
    lastAIDecision,
  };
}

export default function SafetyPanel({
  towerId = null,
  areaId = null,
}) {
  // Use towerId if available, otherwise areaId, for consistent metrics
  const id = towerId || areaId;
  const metrics = generateSystemMetrics(id);

  const readinessColor =
    metrics.actionReadiness >= 0.85 ? "#22c55e" : 
    metrics.actionReadiness >= 0.7 ? "#f59e0b" : "#ef4444";

  const modeColor =
    metrics.automationMode === "Active" ? "#22c55e" :
    metrics.automationMode === "Monitoring" ? "#f59e0b" : "#ef4444";

  return (
    <div
      style={{
        background: "rgba(255,255,255,0.03)",
        border: "1px solid rgba(255,255,255,0.08)",
        borderRadius: 12,
        padding: 12,
        marginTop: 28,
        marginBottom: 12,
      }}
    >
      <div style={{ fontWeight: 900, marginBottom: 10 }}>
        Autonomous Safety Monitor
      </div>

      <StatusRow
        label="Action Readiness"
        value={`${Math.round(metrics.actionReadiness * 100)}%`}
        color={readinessColor}
      />

      <StatusRow
        label="Affected Radius"
        value={`${metrics.affectedRadius.toFixed(1)} km`}
        color="#f59e0b"
      />

      <StatusRow
        label="Automation Mode"
        value={metrics.automationMode}
        color={modeColor}
      />

      <StatusRow
        label="Rollback Available"
        value={metrics.rollbackAvailable ? "Yes" : "No"}
        color={metrics.rollbackAvailable ? "#22c55e" : "#ef4444"}
      />

      <StatusRow
        label="Last AI Decision"
        value={metrics.lastAIDecision}
        color="#f59e0b"
      />
    </div>
  );
}

