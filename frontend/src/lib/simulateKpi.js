// Deterministic per-tower KPI simulation, ported from the backend's /api/kpis
// stub (backend/app.py) so the coverage map works without a running server.

function hashString(str) {
  let h = 0;
  for (let i = 0; i < str.length; i++) {
    h = (Math.imul(31, h) + str.charCodeAt(i)) | 0;
  }
  return Math.abs(h) % 10000 / 10000;
}

export function simulateKpi(towerId) {
  const h = hashString(String(towerId));
  return {
    traffic: 0.3 + h * 0.6,
    latency_ms: Math.round(20 + h * 80),
    packet_loss: Math.round((0.005 + h * 0.03) * 10000) / 10000,
    energy: 0.5 + h * 0.4,
    status: h > 0.9 ? "down" : h > 0.7 ? "degraded" : "ok",
  };
}
