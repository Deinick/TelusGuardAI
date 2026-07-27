import { useEffect, useMemo, useState, useCallback } from "react";
import L from "leaflet";
import EventPanel from "../components/EventPanel";
import CoverageMap from "../components/CoverageMap";
import DetailsPanel from "../components/DetailsPanel";
import ImpactAreaReport from "../components/ImpactAreaReport";
import EmptySelectionPanel from "../components/EmptySelectionPanel";
import SafetyPanel from "../components/SafetyPanel";
import { simulateKpi } from "../lib/simulateKpi.js";
import { MOCK_AGENT_RESPONSE } from "../lib/mockAgentResponse.js";

const center = [56.1304, -106.3468];

function countTowersInArea(area, towers) {
  if (!towers?.length || !area.bounds?.[0] || !area.bounds?.[1]) return 0;
  const [sw, ne] = area.bounds;
  const bounds = L.latLngBounds(sw, ne);
  return towers.filter((t) => t.lat != null && t.lon != null && bounds.contains(L.latLng(t.lat, t.lon))).length;
}

function severityToScore(sev) {
  const s = (sev || "").toLowerCase();
  if (s === "critical") return 0.95;
  if (s === "high") return 0.8;
  if (s === "moderate") return 0.6;
  if (s === "low") return 0.35;
  return 0.5;
}

export default function DashboardPage({
  onAnalyze,
  loading,
  error,
  agentResponse,
}) {
  const [selectedTower, setSelectedTower] = useState(null);
  const [radio, setRadio] = useState("ALL");
  const [layers, setLayers] = useState({ towers: true, heatmap: true, zones: true });
  const [selectedAreaId, setSelectedAreaId] = useState(null);
  const [focusBounds, setFocusBounds] = useState(null);

  // Tower dataset (~17k towers, ~2.7MB) is fetched at runtime from /public
  // rather than bundled into the JS chunk, so the app starts up fast.
  const [towersData, setTowersData] = useState([]);
  const [towersLoading, setTowersLoading] = useState(true);
  const [towersError, setTowersError] = useState(null);

  useEffect(() => {
    fetch(`${import.meta.env.BASE_URL}telus_towers.json`)
      .then((res) => {
        if (!res.ok) throw new Error(`Failed to load tower data: ${res.status}`);
        return res.json();
      })
      .then((data) => setTowersData(data))
      .catch((e) => setTowersError(e.message || String(e)))
      .finally(() => setTowersLoading(false));
  }, []);

  const activeResponse = agentResponse ?? MOCK_AGENT_RESPONSE;

  const radios = useMemo(() => {
    if (!towersData?.length) return ["ALL"];
    const uniq = [...new Set(towersData.map((t) => t.radio).filter(Boolean))];
    return ["ALL", ...uniq.sort()];
  }, [towersData]);

  const filtered = useMemo(() => {
    if (!towersData?.length) return [];
    if (radio === "ALL") return towersData;
    return towersData.filter((t) => t.radio === radio);
  }, [radio, towersData]);

  // Render every tower in the filtered set; CoverageMap uses Leaflet's
  // canvas renderer so this stays smooth even at ~17k markers.
  const toRender = filtered;

  const impactAreas = useMemo(() => {
    const events = activeResponse?.events ?? [];
    const out = [];
    for (const ev of events) {
      const evId = ev.event_id ?? ev.event_name ?? "event";
      for (const a of ev.affected_areas ?? []) {
        if (!Array.isArray(a.lat_range) || a.lat_range.length !== 2) continue;
        if (!Array.isArray(a.long_range) || a.long_range.length !== 2) continue;
        const minLat = Math.min(a.lat_range[0], a.lat_range[1]);
        const maxLat = Math.max(a.lat_range[0], a.lat_range[1]);
        const minLon = Math.min(a.long_range[0], a.long_range[1]);
        const maxLon = Math.max(a.long_range[0], a.long_range[1]);
        const id = `${evId}::${a.area_name ?? a.area ?? "area"}`;
        const severity = (a.severity ?? a.severity_level ?? "moderate").toLowerCase();
        out.push({
          id,
          name: a.area_name ?? a.area ?? id,
          eventName: ev.event_name ?? evId,
          severity,
          severityScore: severityToScore(severity),
          confidence: a.confidence,
          affectedCount: Array.isArray(a.affected_towers) ? a.affected_towers.length : null,
          reasoning: a.reasoning,
          estimated_impact: a.estimated_impact,
          mitigation: a.mitigation_actions || a.mitigation,
          bounds: [
            [minLat, minLon],
            [maxLat, maxLon],
          ],
        });
      }
    }
    out.sort((x, y) => y.severityScore - x.severityScore);
    return out;
  }, [activeResponse]);

  const impactAreasWithCounts = useMemo(() => {
    // Use filtered towers (toRender) to match what's displayed on the map
    if (!toRender?.length) return impactAreas.map((a) => ({ ...a, towerCount: 0 }));
    return impactAreas.map((a) => ({ ...a, towerCount: countTowersInArea(a, toRender) }));
  }, [impactAreas, toRender]);

  // Reset local selection whenever a new analysis result arrives, following
  // React's recommended "adjust state during render" pattern instead of an
  // effect (https://react.dev/learn/you-might-not-need-an-effect).
  const [prevAgentResponse, setPrevAgentResponse] = useState(agentResponse);
  if (agentResponse !== prevAgentResponse) {
    setPrevAgentResponse(agentResponse);
    if (agentResponse) {
      setSelectedAreaId(null);
      setSelectedTower(null);
      setFocusBounds(null);
    }
  }

  const getTowerId = useCallback((t) => t.id ?? `tower_${Math.round(t.lat * 1e6)}_${Math.round(t.lon * 1e6)}`, []);

  const selectImpactArea = useCallback(
    (area) => {
      setSelectedAreaId(area.id);
      setFocusBounds(area.bounds);
      setSelectedTower(null);
    },
    [setSelectedTower]
  );

  // KPIs are simulated client-side (the backend's KPIService is a
  // deterministic stub too), so the map works standalone with no server.
  // `tick` advances every 5s, giving values a slight "live" drift that
  // mirrors the original 5s polling behavior.
  const [tick, setTick] = useState(0);
  useEffect(() => {
    const intervalId = setInterval(() => setTick((t) => t + 1), 5000);
    return () => clearInterval(intervalId);
  }, []);

  const kpiByTowerId = useMemo(() => {
    const next = {};
    for (const tower of toRender) {
      next[getTowerId(tower)] = simulateKpi(getTowerId(tower), tick);
    }
    return next;
  }, [toRender, getTowerId, tick]);

  const handleSelectTower = useCallback(
    (towerId) => {
      const tower = toRender.find((t) => getTowerId(t) === towerId);
      if (!tower) {
        setSelectedTower(null);
        return;
      }
      // Store only tower data, NOT KPI snapshot
      // KPI will be looked up fresh from kpiByTowerId when rendering
      // This ensures both popup and panel always use the latest KPI data
      // Polling effect will automatically start fetching KPIs for this tower
      setSelectedTower({ ...tower });
      setSelectedAreaId(null);
      setFocusBounds(null);
    },
    [toRender, getTowerId, setSelectedTower]
  );

  const handleSelectArea = useCallback(
    (areaId) => {
      const area = impactAreasWithCounts.find((a) => a.id === areaId);
      if (area) selectImpactArea(area);
      else setSelectedAreaId(areaId);
    },
    [impactAreasWithCounts, selectImpactArea]
  );

  return (
    <div className="noc-shell">
      <div className="noc-grid">
        {/* LEFT COLUMN */}
        <div className="noc-col noc-left">
          <div className="noc-col-inner">
            <div className="noc-section">
              <div className="noc-title">Event Analysis</div>
              <EventPanel onAnalyze={onAnalyze} loading={loading} />
            </div>
          </div>
        </div>

        {/* CENTER COLUMN */}
        <div className="noc-col noc-center">
          <div className="noc-col-inner">
            <div
              className="noc-section"
              style={{
                display: "flex",
                flexWrap: "wrap",
                gap: 12,
                alignItems: "center",
              }}
            >
              <div style={{ flex: 1 }}>
                <div className="noc-title" style={{ margin: 0 }}>
                  Network Coverage Map
                </div>
                <div className="noc-muted" style={{ fontSize: 12, marginTop: 2 }}>
                  {towersLoading
                    ? "Loading tower data…"
                    : towersError
                    ? `Failed to load tower data: ${towersError}`
                    : `${toRender.length} / ${filtered.length} towers`}
                </div>
              </div>

              {/* Map controls: Radio + layer toggles */}
              <div style={{ display: "flex", flexWrap: "wrap", gap: 10, alignItems: "center" }}>
                <label style={{ display: "flex", alignItems: "center", gap: 6 }}>
                  <span className="noc-muted" style={{ fontSize: 12 }}>Signal:</span>
                  <select
                    value={radio}
                    onChange={(e) => setRadio(e.target.value)}
                    style={{
                      padding: "6px 10px",
                      borderRadius: 8,
                      border: "1px solid var(--border)",
                      background: "rgba(255,255,255,0.06)",
                      color: "inherit",
                      fontSize: 13,
                    }}
                  >
                    {radios.map((r) => (
                      <option key={r} value={r}>
                        {r}
                      </option>
                    ))}
                  </select>
                </label>

                <label style={{ display: "flex", gap: 6, alignItems: "center", fontSize: 13, cursor: "pointer" }}>
                  <input
                    type="checkbox"
                    checked={layers.towers}
                    onChange={(e) => setLayers((p) => ({ ...p, towers: e.target.checked }))}
                  />
                  Towers
                </label>
                <label style={{ display: "flex", gap: 6, alignItems: "center", fontSize: 13, cursor: "pointer" }}>
                  <input
                    type="checkbox"
                    checked={layers.heatmap}
                    onChange={(e) => setLayers((p) => ({ ...p, heatmap: e.target.checked }))}
                  />
                  Heatmap
                </label>
                <label style={{ display: "flex", gap: 6, alignItems: "center", fontSize: 13, cursor: "pointer" }}>
                  <input
                    type="checkbox"
                    checked={layers.zones}
                    onChange={(e) => setLayers((p) => ({ ...p, zones: e.target.checked }))}
                  />
                  Impact areas
                </label>
              </div>
            </div>

            <div style={{ padding: 12, height: "100%" }}>
              <div
                style={{
                  height: "calc(100vh - 96px)",
                  borderRadius: 12,
                  overflow: "hidden",
                }}
              >
                <CoverageMap
                  towers={toRender}
                  center={center}
                  zoom={4}
                  kpiByTowerId={kpiByTowerId}
                  getTowerId={getTowerId}
                  agentResponse={activeResponse}
                  layers={layers}
                  selectedAreaId={selectedAreaId}
                  focusBounds={focusBounds}
                  impactAreas={impactAreasWithCounts}
                  onSelectImpactArea={selectImpactArea}
                  onSelectTower={handleSelectTower}
                  onSelectArea={handleSelectArea}
                  hideControls={true}
                />
              </div>
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN */}
        <div className="noc-col noc-right">
          <div className="noc-col-inner">
            <div className="noc-section">
              {selectedTower ? (
                <>
                  <DetailsPanel 
                    tower={selectedTower} kpiByTowerId={kpiByTowerId} getTowerId={getTowerId}
                  />
                  <SafetyPanel
                    towerId={getTowerId(selectedTower)}
                  />
                </>
              ) : selectedAreaId ? (
                (() => {
                  const selectedArea = impactAreasWithCounts.find((a) => a.id === selectedAreaId);
                  return selectedArea ? (
                    <ImpactAreaReport area={selectedArea} />
                  ) : (
                    <EmptySelectionPanel />
                  );
                })()
              ) : (
                <EmptySelectionPanel />
              )}

              {error && (
                <div style={{ color: "#f87171", marginTop: 10 }}>
                  {error}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
