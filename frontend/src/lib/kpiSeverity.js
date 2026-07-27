// Shared function to calculate severity score from a KPI snapshot.
// This is the single source of truth for severity calculation.
export function calculateSeverityFromKPI(kpi) {
  if (!kpi) return 0;

  // Priority: status > traffic
  if (kpi.status === "down") return 0.95; // Critical (red)
  if (kpi.status === "degraded") return 0.75; // Warning (orange)
  if (kpi.status === "ok") return 0.3; // Online (green)

  // Fallback to traffic-based severity
  const traffic = kpi.traffic;
  if (traffic == null) return 0;
  if (traffic > 0.8) return 0.9; // High traffic = high severity
  if (traffic > 0.5) return 0.65; // Medium traffic = medium severity
  return 0.35; // Low traffic = low severity
}
