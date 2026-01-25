import { useEffect, useMemo, useState, useRef, useCallback } from "react";
import { Link } from "react-router-dom";
import towersData from "../data/telus_towers.json";
import CoverageMap from "../components/CoverageMap.jsx";
import L from "leaflet";

// Helper function to count towers inside an impact area
function countTowersInArea(area, towers) {
  if (!towers || towers.length === 0) return 0;
  if (!area.bounds || !Array.isArray(area.bounds) || area.bounds.length !== 2) return 0;

  // Create Leaflet bounds from area bounds
  // area.bounds is [[minLat, minLon], [maxLat, maxLon]]
  const [southWest, northEast] = area.bounds;
  const bounds = L.latLngBounds(southWest, northEast);

  // Count towers that fall within the bounds
  let count = 0;
  for (const tower of towers) {
    if (tower.lat != null && tower.lon != null) {
      const point = L.latLng(tower.lat, tower.lon);
      // contains() includes points on the boundary
      if (bounds.contains(point)) {
        count++;
      }
    }
  }

  return count;
}

// Map severity label to a numeric score so we can sort
function severityToScore(sev) {
  const s = (sev || "").toLowerCase();
  if (s === "critical") return 0.95;
  if (s === "high") return 0.8;
  if (s === "moderate") return 0.6;
  if (s === "low") return 0.35;
  return 0.5;
}

export default function CoverageMapPage() {
  // Filters
  const [radio, setRadio] = useState("ALL");

  // KPI state from backend
  const [kpiByTowerId, setKpiByTowerId] = useState({});

  // UI state
  const [layers, setLayers] = useState({ towers: true, heatmap: true, zones: true });
  const [selectedTower, setSelectedTower] = useState(null);

  // NEW: selection for areas + focusing bounds
  const [selectedAreaId, setSelectedAreaId] = useState(null);
  const [focusBounds, setFocusBounds] = useState(null);

  // ============================
  // Backend Agent Integration
  const [prompt, setPrompt] = useState(
    "Ice storm in Toronto tonight — which areas will be impacted most?"
  );
  const [agentResponse, setAgentResponse] = useState(null);
  const [isRunning, setIsRunning] = useState(false);
  const [agentError, setAgentError] = useState(null);

  const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:5001";
  const ANALYZE_PATH = "/api/analyze-network-impact";
  const KPIS_PATH = "/api/kpis";  

  async function runAgent() {
    try {
      setIsRunning(true);
      setAgentError(null);
  
      const res = await fetch(`${API_BASE}${ANALYZE_PATH}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: prompt,
          options: {
            max_areas: 10,
            min_confidence: 0.7,
            include_reasoning: true,
          },
        }),
      });
  
      if (!res.ok) {
        const text = await res.text();
        throw new Error(`Backend ${res.status}: ${text}`);
      }
  
      const data = await res.json();
      setAgentResponse(data);
    } catch (e) {
      setAgentError(e.message || String(e));
    } finally {
      setIsRunning(false);
    }
  }
  

  // Use backend response if available; otherwise fallback to mock (so the demo never breaks)
  // ============================

  // Map center (Canada-ish). We'll auto-zoom when selecting an area anyway.
  const center = [56.1304, -106.3468];

  const radios = useMemo(() => {
    const set = new Set(towersData.map((t) => t.radio));
    return ["ALL", ...Array.from(set)];
  }, []);

  const filtered = useMemo(() => {
    if (radio === "ALL") return towersData;
    return towersData.filter((t) => t.radio === radio);
  }, [radio]);

  // Performance cap
  const MAX_RENDER = 5000;
  const toRender = filtered.slice(0, MAX_RENDER);

  // Mock agent/model response
  const mockAgentResponse = useMemo(
    () => ({
      events: [
        // ===== Event 1: BC Place (concert) =====
        {
          event_id: "event_bc_place",
          event_name: "Concert at BC Place",
          affected_areas: [
            {
              area_name: "BC Place / Stadium District",
              center: { latitude: 49.2767, longitude: -123.1119 },
              lat_range: [49.2725, 49.2810],
              long_range: [-123.1180, -123.1050],
              severity: "critical",
              confidence: 0.82,
              estimated_impact: "~12,000 users",
              reasoning:
                "High event intensity near the stadium combined with elevated baseline traffic on nearby towers.",
              affected_towers: ["T_102", "T_087", "T_144"],
              mitigation_actions: ["load-balance to adjacent towers", "reserve simulated capacity for peak window"],
            },
          ],
        },

        // ===== Event 2: Toronto Ice Storm =====
        {
          event_id: "evt_ice_storm_toronto",
          event_name: "Ice Storm – Toronto",
          affected_areas: [
            {
              area_name: "Downtown Toronto Core",
              severity: "critical",
              lat_range: [43.64, 43.68],
              long_range: [-79.4, -79.36],
              center: { lat: 43.66, lon: -79.38 },
              confidence: 0.94,
              estimated_impact: "~15,000 users",
              reasoning:
                "Severe weather impact combined with power instability caused multiple towers to operate near failure thresholds.",
              affected_towers: ["T_A", "T_B", "T_C", "T_D", "T_E", "T_F", "T_G", "T_H", "T_I", "T_J", "T_K", "T_L"],
            },
            {
              area_name: "Scarborough East",
              severity: "moderate",
              lat_range: [43.75, 43.79],
              long_range: [-79.22, -79.18],
              center: { lat: 43.77, lon: -79.2 },
              confidence: 0.76,
              estimated_impact: "~5,000 users",
              reasoning: "Secondary impact from grid instability and reduced backhaul capacity during peak load.",
              affected_towers: ["T_1", "T_2", "T_3", "T_4", "T_5"],
            },
          ],
        },
      ],
    }),
    []
  );

  const activeResponse = agentResponse ?? mockAgentResponse;

  // Clear selections when a new agent response arrives
  useEffect(() => {
    if (agentResponse) {
      setSelectedAreaId(null);
      setSelectedTower(null);
      setFocusBounds(null);
    }
  }, [agentResponse]);

  // Build a sorted list of impact areas (used by map overlay menu)
  const impactAreas = useMemo(() => {
    const events = activeResponse?.events || [];
    const out = [];

    for (const ev of events) {
      const evId = ev.event_id ?? ev.event_name ?? "event";
      for (const a of ev.affected_areas || []) {
        if (!Array.isArray(a.lat_range) || a.lat_range.length !== 2) continue;
        if (!Array.isArray(a.long_range) || a.long_range.length !== 2) continue;

        const minLat = Math.min(a.lat_range[0], a.lat_range[1]);
        const maxLat = Math.max(a.lat_range[0], a.lat_range[1]);
        const minLon = Math.min(a.long_range[0], a.long_range[1]);
        const maxLon = Math.max(a.long_range[0], a.long_range[1]);

        const id = `${evId}::${a.area_name ?? a.area ?? "area"}`;
        const severity = (a.severity ?? a.severity_level ?? "moderate").toLowerCase();
        const confidence = a.confidence;

        out.push({
          id,
          name: a.area_name ?? a.area ?? id,
          eventName: ev.event_name ?? evId,
          severity,
          severityScore: severityToScore(severity),
          confidence,
          affectedCount: Array.isArray(a.affected_towers) ? a.affected_towers.length : null,
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

  // Compute tower counts for impact areas
  const impactAreasWithCounts = useMemo(() => {
    if (!towersData || towersData.length === 0) {
      return impactAreas.map(area => ({ ...area, towerCount: 0 }));
    }

    return impactAreas.map(area => {
      const towerCount = countTowersInArea(area, towersData);
      return { ...area, towerCount };
    });
  }, [impactAreas, towersData]);

  const selectImpactArea = (area) => {
    setSelectedAreaId(area.id);
    setFocusBounds(area.bounds);
    setSelectedTower(null);
  };

  // Helper to get stable tower_id (towers already have id field)
  const getTowerId = useCallback((tower) => {
    if (tower.id) return tower.id;
    // Fallback: generate from lat/lon if id missing
    return `tower_${Math.round(tower.lat * 1000000)}_${Math.round(tower.lon * 1000000)}`;
  }, []);

  // State for map bounds tracking
  const [mapBounds, setMapBounds] = useState(null);
  const [fetchInProgress, setFetchInProgress] = useState(false);
  const throttleRef = useRef({ lastRun: 0 });

  // Fetch KPIs for visible towers
  const fetchKPIs = async (towerIds) => {
    if (!towerIds || towerIds.length === 0) return;
    if (fetchInProgress) return;

    // Cap at 1000 towers per request
    const cappedIds = towerIds.slice(0, 1000);

    try {
      setFetchInProgress(true);
      const res = await fetch(`${API_BASE}${KPIS_PATH}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          tower_ids: cappedIds,
          options: {
            mode: "sim",
            tick_ms: 1000,
          },
        }),
      });

      if (!res.ok) {
        const text = await res.text();
        console.error(`KPI fetch failed ${res.status}: ${text}`);
        return;
      }

      const data = await res.json();
      if (data.kpis) {
        setKpiByTowerId((prev) => ({ ...prev, ...data.kpis }));
        if (import.meta.env.DEV) {
          console.log(`[KPI] Fetched ${Object.keys(data.kpis).length} KPIs`);
        }
      }
    } catch (e) {
      console.error("Error fetching KPIs:", e);
    } finally {
      setFetchInProgress(false);
    }
  };

  // Throttled fetch function (1.5 seconds)
  const throttledFetchKPIs = (towerIds) => {
    const now = Date.now();
    if (now - throttleRef.current.lastRun >= 1500) {
      throttleRef.current.lastRun = now;
      fetchKPIs(towerIds);
    }
  };

  // Compute visible towers when map bounds change
  useEffect(() => {
    if (!mapBounds) return;

    const visibleTowerIds = toRender
      .filter((tower) => {
        const lat = tower.lat;
        const lon = tower.lon;
        return (
          lat >= mapBounds.south &&
          lat <= mapBounds.north &&
          lon >= mapBounds.west &&
          lon <= mapBounds.east
        );
      })
      .map(getTowerId);

    if (visibleTowerIds.length > 0) {
      throttledFetchKPIs(visibleTowerIds);
    }
  }, [mapBounds, toRender, getTowerId]);

  return (
    <div style={{ padding: 16 }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
        <div>
          <h1 style={{ margin: 0 }}>TELUS Towers – Live KPIs + Impact Areas</h1>
          <p style={{ marginTop: 6, opacity: 0.75 }}>
            Showing {toRender.length} / {filtered.length} towers
          </p>
        </div>
        <Link to="/">Back</Link>
      </div>

      {/* Controls */}
      <div style={{ display: "flex", flexWrap: "wrap", gap: 14, alignItems: "center", margin: "12px 0" }}>
        <label>
          Radio:
          <select value={radio} onChange={(e) => setRadio(e.target.value)} style={{ marginLeft: 8 }}>
            {radios.map((r) => (
              <option key={r} value={r}>
                {r}
              </option>
            ))}
          </select>
        </label>

        {/* Layer toggles */}
        <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
          <label style={{ display: "flex", gap: 6, alignItems: "center" }}>
            <input
              type="checkbox"
              checked={layers.towers}
              onChange={(e) => setLayers((p) => ({ ...p, towers: e.target.checked }))}
            />
            Towers
          </label>

          <label style={{ display: "flex", gap: 6, alignItems: "center" }}>
            <input
              type="checkbox"
              checked={layers.heatmap}
              onChange={(e) => setLayers((p) => ({ ...p, heatmap: e.target.checked }))}
            />
            Heatmap
          </label>

          <label style={{ display: "flex", gap: 6, alignItems: "center" }}>
            <input
              type="checkbox"
              checked={layers.zones}
              onChange={(e) => setLayers((p) => ({ ...p, zones: e.target.checked }))}
            />
            Impact Areas
          </label>
        </div>

        {/* Prompt + run */}
        <input
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Describe an event..."
          style={{
            minWidth: 420,
            padding: "6px 10px",
            borderRadius: 8,
            border: "1px solid rgba(255,255,255,0.2)",
            background: "rgba(255,255,255,0.06)",
            color: "inherit",
          }}
        />

        <button
          onClick={runAgent}
          disabled={isRunning}
          style={{
            padding: "6px 10px",
            borderRadius: 8,
            cursor: isRunning ? "not-allowed" : "pointer",
            opacity: isRunning ? 0.7 : 1,
          }}
          title={`POST ${API_BASE}${ANALYZE_PATH}`}
        >
          {isRunning ? "Analyzing..." : "Run analysis"}
        </button>

        {agentError && (
          <div style={{ color: "#ff6b6b", maxWidth: 520 }}>
            {agentError}
          </div>
        )}

        {/* Selection info */}
        {selectedTower && (
          <div style={{ opacity: 0.85 }}>
            Selected tower: <b>{selectedTower}</b>
          </div>
        )}
        {selectedAreaId && (
          <div style={{ opacity: 0.85 }}>
            Selected area: <b>{selectedAreaId}</b>
          </div>
        )}

        <div style={{ opacity: 0.75 }}>
          KPIs from backend
          {agentResponse ? " (Agent: backend)" : " (Agent: mock)"}
        </div>
      </div>

      {/* Map */}
      <div>
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
          onMapBoundsChange={setMapBounds}
          onSelectTower={(id) => {
            setSelectedTower(id);
            setSelectedAreaId(null);
            setFocusBounds(null);
          }}
          onSelectArea={(areaId) => {
            const area = impactAreas.find((x) => x.id === areaId);
            if (area) selectImpactArea(area);
            else setSelectedAreaId(areaId);
          }}
        />
      </div>
    </div>
  );
}
