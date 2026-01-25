import { useEffect, useMemo, useState, useRef } from "react";
import { MapContainer, TileLayer, CircleMarker, Popup, Rectangle, useMap, useMapEvents } from "react-leaflet";
import "leaflet.heat";
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

// Tower status/KPI -> color
function colorFromKPI(kpi) {
  if (!kpi) return "#3388ff"; // Default blue if no KPI
  
  // Use status if available
  if (kpi.status === "down") return "#e53935"; // Red
  if (kpi.status === "degraded") return "#fb8c00"; // Orange
  if (kpi.status === "ok") return "#43a047"; // Green
  
  // Fallback to traffic-based coloring
  const traffic = kpi.traffic;
  if (traffic == null) return "#3388ff";
  if (traffic > 0.8) return "#e53935";
  if (traffic > 0.5) return "#fb8c00";
  return "#43a047";
}

// severity label -> numeric 0..1
function severityToScore(sev) {
  const s = (sev || "").toLowerCase();
  if (s === "critical") return 0.95;
  if (s === "high") return 0.8;
  if (s === "moderate") return 0.6;
  if (s === "low") return 0.35;
  const n = Number(sev);
  return Number.isFinite(n) ? Math.max(0, Math.min(1, n)) : 0.5;
}

// severity label -> outline color
function colorFromSeverityLabel(sev) {
  const s = severityToScore(sev);
  if (s > 0.85) return "#d32f2f";
  if (s > 0.65) return "#f57c00";
  return "#388e3c";
}

function FitBounds({ bounds }) {
  const map = useMap();
  useEffect(() => {
    if (!bounds) return;
    map.fitBounds(bounds, { padding: [40, 40] });
  }, [map, bounds]);
  return null;
}

// Wrapper component to ensure proper z-ordering for overlapping impact areas
function ZOrderedRectangle({ area, isSelected, onSelectArea, children }) {
  const rectangleRef = useRef(null);

  useEffect(() => {
    // Use setTimeout to ensure the layer is fully added to the map before bringing to front
    const timer = setTimeout(() => {
      if (rectangleRef.current) {
        const layer = rectangleRef.current.leafletElement;
        if (layer) {
          // Bring this rectangle to front to ensure it receives click events
          // This is especially important for smaller areas inside larger ones
          layer.bringToFront();
        }
      }
    }, 0);
    return () => clearTimeout(timer);
  }, [area.id]);

  return (
    <Rectangle
      ref={rectangleRef}
      bounds={area.bounds}
      pathOptions={{
        color: colorFromSeverityLabel(area.severityLabel),
        weight: isSelected ? 5 : 2,
        fillOpacity: isSelected ? 0.22 : 0.12,
        // Ensure pointer events work correctly
        interactive: true,
      }}
      eventHandlers={{
        click: (e) => {
          // Stop event propagation to prevent parent areas from receiving the click
          if (e.originalEvent) {
            e.originalEvent.stopPropagation();
          }
          onSelectArea?.(area.id);
        },
        mousedown: (e) => {
          // Also stop propagation on mousedown to be safe
          if (e.originalEvent) {
            e.originalEvent.stopPropagation();
          }
        },
      }}
    >
      {children}
    </Rectangle>
  );
}

// Component to track map bounds changes
function MapBoundsTracker({ onBoundsChange }) {
  const map = useMap();
  
  useMapEvents({
    moveend: () => {
      const bounds = map.getBounds();
      if (onBoundsChange) {
        onBoundsChange({
          north: bounds.getNorth(),
          south: bounds.getSouth(),
          east: bounds.getEast(),
          west: bounds.getWest(),
        });
      }
    },
    zoomend: () => {
      const bounds = map.getBounds();
      if (onBoundsChange) {
        onBoundsChange({
          north: bounds.getNorth(),
          south: bounds.getSouth(),
          east: bounds.getEast(),
          west: bounds.getWest(),
        });
      }
    },
  });
  
  // Initial bounds
  useEffect(() => {
    const bounds = map.getBounds();
    if (onBoundsChange) {
      onBoundsChange({
        north: bounds.getNorth(),
        south: bounds.getSouth(),
        east: bounds.getEast(),
        west: bounds.getWest(),
      });
    }
  }, [map, onBoundsChange]);
  
  return null;
}

// Heat layer wrapper (Leaflet.heat). Expects points: [{lat, lon, intensity}] intensity 0..1
function HeatLayer({ points, enabled }) {
  const map = useMap();

  const heatData = useMemo(() => {
    if (!enabled) return [];
    return (points || []).map((p) => [
      p.lat,
      p.lon,
      Math.max(0, Math.min(1, p.intensity ?? p.severity ?? 0.5)),
    ]);
  }, [points, enabled]);

  useEffect(() => {
    if (!enabled) return;

    const layer = L.heatLayer(heatData, {
      radius: 25,
      blur: 18,
      maxZoom: 12,
    });

    layer.addTo(map);
    return () => map.removeLayer(layer);
  }, [map, enabled, heatData]);

  return null;
}

// Impact Areas overlay menu component
function ImpactAreasMenu({ impactAreas, selectedAreaId, onSelectImpactArea, isOpen, onToggle }) {
  const hasAreas = impactAreas && impactAreas.length > 0;

  return (
    <div
      data-impact-areas-menu
      style={{
        position: "absolute",
        top: 12,
        right: 12,
        zIndex: 1000,
        display: "flex",
        flexDirection: "column",
        alignItems: "flex-end",
      }}
    >
      {/* Toggle button */}
      <button
        onClick={(e) => {
          e.stopPropagation();
          onToggle();
        }}
        onMouseDown={(e) => e.stopPropagation()}
        style={{
          padding: "8px 14px",
          borderRadius: 8,
          border: "1px solid rgba(255,255,255,0.14)",
          background: "rgba(0,0,0,0.6)",
          color: "#e9ecf1",
          cursor: "pointer",
          fontSize: 14,
          fontWeight: 500,
          backdropFilter: "blur(8px)",
          boxShadow: "0 2px 8px rgba(0,0,0,0.3)",
        }}
      >
        Impact Areas
      </button>

      {/* Menu panel */}
      {isOpen && (
        <div
          onMouseDown={(e) => e.stopPropagation()}
          onClick={(e) => e.stopPropagation()}
          style={{
            marginTop: 8,
            width: 320,
            maxHeight: "60vh",
            overflowY: "auto",
            borderRadius: 12,
            border: "1px solid rgba(255,255,255,0.12)",
            background: "rgba(0,0,0,0.75)",
            backdropFilter: "blur(12px)",
            padding: 12,
            boxShadow: "0 4px 16px rgba(0,0,0,0.4)",
          }}
        >
          <div style={{ fontWeight: 750, marginBottom: 8, fontSize: 16 }}>Impact Areas</div>

          {hasAreas ? (
            <>
              {/* Legend */}
              <div style={{ display: "flex", gap: 10, alignItems: "center", opacity: 0.9, marginBottom: 10 }}>
                <span>🟢 low</span>
                <span>🟠 medium</span>
                <span>🔴 critical</span>
              </div>

              {impactAreas.map((a) => {
            const isSelected = a.id === selectedAreaId;
            const dot = a.severity === "critical" ? "🔴" : a.severity === "high" ? "🟠" : "🟢";
            const confPct =
              a.confidence != null
                ? typeof a.confidence === "number"
                  ? `${Math.round(a.confidence * 100)}%`
                  : String(a.confidence)
                : "—";
            const towersTxt = a.affectedCount != null ? String(a.affectedCount) : "—";

            return (
              <button
                key={a.id}
                onClick={(e) => {
                  e.stopPropagation();
                  onSelectImpactArea(a);
                }}
                onMouseDown={(e) => e.stopPropagation()}
                style={{
                  width: "100%",
                  textAlign: "left",
                  border: "1px solid rgba(255,255,255,0.12)",
                  background: isSelected ? "rgba(255,255,255,0.08)" : "transparent",
                  padding: 10,
                  borderRadius: 10,
                  marginBottom: 10,
                  cursor: "pointer",
                  color: "inherit",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", gap: 10 }}>
                  <div style={{ fontWeight: 650 }}>
                    {dot} {a.name}
                  </div>
                  <div style={{ opacity: 0.75 }}>{a.severity}</div>
                </div>

                <div style={{ opacity: 0.7, marginTop: 4, fontSize: 12 }}>{a.eventName}</div>

                <div style={{ display: "flex", gap: 12, marginTop: 6, opacity: 0.9 }}>
                  <div>
                    Towers: <b>{a.towerCount != null ? a.towerCount : towersTxt}</b>
                  </div>
                  <div>
                    Confidence: <b>{confPct}</b>
                  </div>
                </div>
              </button>
            );
          })}
            </>
          ) : (
            <div style={{ opacity: 0.7 }}>No impact areas yet.</div>
          )}
        </div>
      )}
    </div>
  );
}

// render agent/model response: response.events[].affected_areas[] with lat_range + long_range
export default function CoverageMap({
  towers,
  center,
  zoom = 5,
  kpiByTowerId = {},
  getTowerId,

  // agent response (raw)
  agentResponse = null,

  // toggles
  layers = { towers: true, heatmap: true, zones: true },

  // selection callbacks
  onSelectTower,
  onSelectArea,

  // NEW for UX polish
  selectedAreaId = null,
  focusBounds = null,

  // NEW: impact areas list and selection handler
  impactAreas = [],
  onSelectImpactArea,
  
  // NEW: map bounds tracking
  onMapBoundsChange,
}) {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  // Close menu when clicking outside
  useEffect(() => {
    if (!isMenuOpen) return;

    const handleClickOutside = (e) => {
      // Check if click is outside the menu
      const menuElement = e.target.closest('[data-impact-areas-menu]');
      if (!menuElement) {
        setIsMenuOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [isMenuOpen]);

  // Flatten affected areas from agent response
  const affectedAreas = useMemo(() => {
    const events = agentResponse?.events || [];
    const areas = [];

    for (const ev of events) {
      const evId = ev.event_id ?? ev.event_name ?? "event";
      const list = ev.affected_areas || [];

      for (const a of list) {
        const id = `${evId}::${a.area_name ?? a.area ?? "area"}`;
        const latRange = a.lat_range;
        const lonRange = a.long_range;

        if (!Array.isArray(latRange) || latRange.length !== 2) continue;
        if (!Array.isArray(lonRange) || lonRange.length !== 2) continue;

        const minLat = Math.min(latRange[0], latRange[1]);
        const maxLat = Math.max(latRange[0], latRange[1]);
        const minLon = Math.min(lonRange[0], lonRange[1]);
        const maxLon = Math.max(lonRange[0], lonRange[1]);

        // Calculate area size for proper z-ordering
        const areaSize = (maxLat - minLat) * (maxLon - minLon);

        areas.push({
          id,
          event_id: evId,
          name: a.area_name ?? a.area ?? id,
          severityLabel: a.severity ?? a.severity_level ?? "moderate",
          severityScore: severityToScore(a.severity ?? a.severity_level),
          center:
            a.center || {
              latitude: (minLat + maxLat) / 2,
              longitude: (minLon + maxLon) / 2,
            },
          bounds: [
            [minLat, minLon],
            [maxLat, maxLon],
          ],
          areaSize, // Store area size for sorting
          confidence: a.confidence,
          reasoning: a.reasoning,
          estimated_impact: a.estimated_impact,
          affected_towers: a.affected_towers,
          mitigation: a.mitigation_actions || a.mitigation,
        });
      }
    }

    // Sort by area size (descending) so larger areas render first, smaller areas render last (on top)
    // For areas of similar size, prioritize higher severity to render last
    // This ensures smaller/higher-priority areas receive click events
    areas.sort((x, y) => {
      // Primary sort: by area size (larger first = renders first, smaller last = renders on top)
      const sizeDiff = y.areaSize - x.areaSize;
      if (Math.abs(sizeDiff) > 0.0001) {
        // Areas are significantly different in size
        return sizeDiff;
      }
      // Secondary sort: by severity (lower severity first = renders first, higher severity last = renders on top)
      return x.severityScore - y.severityScore;
    });
    return areas;
  }, [agentResponse]);

  // Compute tower counts for each impact area
  const areasWithTowerCounts = useMemo(() => {
    if (!towers || towers.length === 0) {
      return affectedAreas.map(area => ({ ...area, towerCount: 0 }));
    }

    return affectedAreas.map(area => {
      const towerCount = countTowersInArea(area, towers);
      return { ...area, towerCount };
    });
  }, [affectedAreas, towers]);

  // Heatmap points from affected area centers
  const heatPoints = useMemo(() => {
    if (!layers.heatmap) return [];
    return affectedAreas
      .map((a) => {
        const lat = a.center?.latitude ?? a.center?.lat;
        const lon = a.center?.longitude ?? a.center?.lon ?? a.center?.long; // supports backend "long"
        if (lat == null || lon == null) return null;
        return { lat, lon, intensity: a.severityScore };
      })
      .filter(Boolean);
  }, [affectedAreas, layers.heatmap]);

  return (
    <div style={{ height: "80vh", width: "100%", position: "relative" }}>
      <MapContainer center={center} zoom={zoom} style={{ height: "100%", width: "100%" }}>
        <TileLayer
          attribution="&copy; OpenStreetMap contributors"
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {/* NEW: auto-zoom to selected area */}
        <FitBounds bounds={focusBounds} />
        
        {/* Track map bounds for KPI fetching */}
        <MapBoundsTracker onBoundsChange={onMapBoundsChange} />

        {/* Heatmap */}
        <HeatLayer points={heatPoints} enabled={!!layers.heatmap} />

        {/* Rectangles for affected areas */}
        {/* Render in order: larger areas first, smaller areas last (on top) */}
        {layers.zones &&
          areasWithTowerCounts.map((a) => {
            const isSelected = selectedAreaId === a.id;

            return (
              <ZOrderedRectangle
                key={a.id}
                area={a}
                isSelected={isSelected}
                onSelectArea={onSelectArea}
              >
                <Popup>
                  <div style={{ fontSize: 13 }}>
                    <div>
                      <b>Area:</b> {a.name}
                    </div>
                    <div>
                      <b>Severity:</b> {String(a.severityLabel)} ({Math.round(a.severityScore * 100)}%)
                    </div>

                    {/* Display tower count */}
                    <div>
                      <b>Towers affected:</b> {a.towerCount ?? 0}
                    </div>

                    {a.confidence != null && (
                      <div>
                        <b>Confidence:</b>{" "}
                        {typeof a.confidence === "number" ? `${Math.round(a.confidence * 100)}%` : String(a.confidence)}
                      </div>
                    )}

                    {a.estimated_impact && (
                      <div>
                        <b>Impact:</b> {a.estimated_impact}
                      </div>
                    )}

                    {Array.isArray(a.affected_towers) && a.affected_towers.length > 0 && (
                      <div style={{ opacity: 0.7, fontSize: 11, marginTop: 4 }}>
                        <i>Backend reported: {a.affected_towers.length} towers</i>
                      </div>
                    )}

                    {a.reasoning && (
                      <>
                        <hr />
                        <div style={{ whiteSpace: "pre-wrap" }}>
                          <b>Why:</b> {a.reasoning}
                        </div>
                      </>
                    )}

                    {a.mitigation && (
                      <>
                        <hr />
                        <div style={{ whiteSpace: "pre-wrap" }}>
                          <b>Mitigation:</b> {JSON.stringify(a.mitigation)}
                        </div>
                      </>
                    )}
                  </div>
                </Popup>
              </ZOrderedRectangle>
            );
          })}

        {/* Towers */}
        {layers.towers &&
          towers.map((t) => {
            const towerId = getTowerId ? getTowerId(t) : t.id;
            const kpi = kpiByTowerId[towerId];

            return (
              <CircleMarker
                key={t.id}
                center={[t.lat, t.lon]}
                radius={4}
                pathOptions={{
                  color: colorFromKPI(kpi),
                  fillOpacity: 0.85,
                }}
                eventHandlers={{
                  click: () => onSelectTower?.(towerId),
                }}
              >
                <Popup>
                  <div style={{ fontSize: 13 }}>
                    <div>
                      <b>ID:</b> {towerId}
                    </div>
                    <div>
                      <b>Radio:</b> {t.radio}
                    </div>

                    {kpi ? (
                      <>
                        <hr />
                        <div>
                          <b>Status:</b> <span style={{ 
                            color: kpi.status === "down" ? "#e53935" : 
                                   kpi.status === "degraded" ? "#fb8c00" : "#43a047"
                          }}>{kpi.status.toUpperCase()}</span>
                        </div>
                        <div>
                          <b>Traffic:</b> {(kpi.traffic * 100).toFixed(1)}%
                        </div>
                        <div>
                          <b>Latency:</b> {kpi.latency_ms} ms
                        </div>
                        <div>
                          <b>Packet Loss:</b> {(kpi.packet_loss * 100).toFixed(2)}%
                        </div>
                        <div>
                          <b>Energy:</b> {(kpi.energy * 100).toFixed(1)}%
                        </div>
                      </>
                    ) : (
                      <div style={{ opacity: 0.6, marginTop: 4, fontStyle: "italic" }}>
                        KPI data loading...
                      </div>
                    )}
                  </div>
                </Popup>
              </CircleMarker>
            );
          })}
      </MapContainer>

      {/* Impact Areas overlay menu */}
      <ImpactAreasMenu
        impactAreas={impactAreas}
        selectedAreaId={selectedAreaId}
        onSelectImpactArea={onSelectImpactArea}
        isOpen={isMenuOpen}
        onToggle={() => setIsMenuOpen(!isMenuOpen)}
      />
    </div>
  );
}
