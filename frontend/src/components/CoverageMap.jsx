import { useEffect, useMemo, useState, useRef } from "react";
import { MapContainer, TileLayer, CircleMarker, Popup, Rectangle, useMap, useMapEvents } from "react-leaflet";
import "leaflet.heat";
import L from "leaflet";
import { calculateSeverityFromKPI } from "../lib/kpiSeverity.js";

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
  const sev = calculateSeverityFromKPI(kpi);
  if (sev >= 0.85) return "#e53935"; // Red
  if (sev >= 0.6) return "#fb8c00"; // Orange
  return "#43a047"; // Green
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

// Get severity color
function getSeverityColor(severity) {
  const s = (severity || "").toLowerCase();
  if (s === "critical") return "#d32f2f"; // red
  if (s === "high") return "#f57c00"; // orange
  if (s === "moderate") return "#fbc02d"; // yellow
  if (s === "low") return "#388e3c"; // green
  return "#757575"; // default gray
}

// Sort impact areas by severity: critical → high → moderate → low
function sortImpactAreasBySeverity(areas) {
  const severityOrder = { critical: 0, high: 1, moderate: 2, low: 3 };
  return [...areas].sort((a, b) => {
    const aOrder = severityOrder[a.severity?.toLowerCase()] ?? 99;
    const bOrder = severityOrder[b.severity?.toLowerCase()] ?? 99;
    return aOrder - bOrder;
  });
}

// Impact Areas Control - renders as a Leaflet control in top-right corner
function ImpactAreasControl({ impactAreas, selectedAreaId, onSelectImpactArea }) {
  const map = useMap();
  const containerRef = useRef(null);
  const controlRef = useRef(null);
  const [isOpen, setIsOpen] = useState(false);

  // Create Leaflet control and add to map
  useEffect(() => {
    if (!map) return;

    const Control = L.Control.extend({
      onAdd: function() {
        const container = L.DomUtil.create("div", "leaflet-bar leaflet-control");
        container.style.background = "transparent";
        container.style.border = "none";
        container.style.boxShadow = "none";
        containerRef.current = container;
        return container;
      },
    });

    const control = new Control({ position: "topright" });
    control.addTo(map);
    controlRef.current = control;

    return () => {
      if (controlRef.current) {
        map.removeControl(controlRef.current);
      }
    };
  }, [map]);

  // Close menu when clicking outside
  useEffect(() => {
    if (!isOpen) return;

    const handleClickOutside = (e) => {
      const menuElement = e.target.closest('[data-impact-areas-control]');
      if (!menuElement && containerRef.current) {
        setIsOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [isOpen]);

  // Sort impact areas by severity
  const sortedAreas = useMemo(() => {
    return sortImpactAreasBySeverity(impactAreas || []);
  }, [impactAreas]);

  const hasAreas = sortedAreas.length > 0;

  // Render control content using DOM manipulation (required for Leaflet controls)
  useEffect(() => {
    if (!containerRef.current) return;

    // Handle area selection (defined inside useEffect to avoid closure issues)
    const handleSelectArea = (area) => {
      if (onSelectImpactArea) {
        onSelectImpactArea(area);
      }
      setIsOpen(false);
    };

    const container = containerRef.current;
    container.innerHTML = "";

    const wrapper = document.createElement("div");
    wrapper.setAttribute("data-impact-areas-control", "");
    wrapper.style.cssText = "display: flex; flex-direction: column; align-items: flex-end;";

    // Toggle button
    const button = document.createElement("button");
    button.textContent = "Impact Areas";
    button.style.cssText = `
      padding: 8px 14px;
      border-radius: 8px;
      border: 1px solid rgba(255,255,255,0.2);
      background: rgba(50, 50, 50, 0.75);
      color: #e9ecf1;
      cursor: pointer;
      font-size: 14px;
      font-weight: 500;
      box-shadow: 0 2px 8px rgba(0,0,0,0.3);
      font-family: inherit;
      line-height: 1.4;
      transition: background 0.2s;
    `;
    L.DomEvent.on(button, "click", (e) => {
      L.DomEvent.stopPropagation(e);
      setIsOpen(!isOpen);
    });
    L.DomEvent.on(button, "mousedown", (e) => {
      L.DomEvent.stopPropagation(e);
    });
    // Hover effect
    button.addEventListener("mouseenter", () => {
      button.style.background = "rgba(50, 50, 50, 0.85)";
    });
    button.addEventListener("mouseleave", () => {
      button.style.background = "rgba(50, 50, 50, 0.75)";
    });

    wrapper.appendChild(button);

    // Dropdown panel
    if (isOpen) {
      const panel = document.createElement("div");
      panel.style.cssText = `
        margin-top: 8px;
        width: 320px;
        max-height: 60vh;
        overflow-y: auto;
        border-radius: 8px;
        border: 1px solid rgba(255,255,255,0.2);
        background: rgba(50, 50, 50, 0.75);
        padding: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        z-index: 1000;
        backdrop-filter: blur(4px);
      `;

      if (hasAreas) {
        sortedAreas.forEach((area, index) => {
          const isSelected = area.id === selectedAreaId;
          const severityColor = getSeverityColor(area.severity);
          const isLast = index === sortedAreas.length - 1;

          const item = document.createElement("button");
          // For selected items: full border on all sides with severity color
          // For non-selected items: subtle border with divider on bottom (except last)
          const borderStyle = isSelected 
            ? `2px solid ${severityColor}` 
            : "1px solid rgba(255,255,255,0.1)";
          const borderBottom = isSelected
            ? `2px solid ${severityColor}`  // Complete border for selected items
            : (!isLast ? "1px solid rgba(255,255,255,0.08)" : "1px solid rgba(255,255,255,0.1)");
          
          item.style.cssText = `
            width: 100%;
            text-align: left;
            border: ${borderStyle};
            border-bottom: ${borderBottom};
            background: ${isSelected ? "rgba(255,255,255,0.15)" : "transparent"};
            padding: 10px 12px;
            border-radius: 6px;
            cursor: pointer;
            color: #e9ecf1;
            font-family: inherit;
            margin-bottom: ${isLast ? "0" : "8px"};
            transition: all 0.2s;
            box-sizing: border-box;
          `;

          const content = document.createElement("div");
          content.style.cssText = "display: flex; align-items: center; gap: 10px; margin-bottom: 4px;";

          const dot = document.createElement("div");
          dot.style.cssText = `
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: ${severityColor};
            flex-shrink: 0;
          `;

          const name = document.createElement("div");
          name.textContent = area.name;
          name.style.cssText = "font-weight: 600; flex: 1; color: #e9ecf1;";

          content.appendChild(dot);
          content.appendChild(name);

          const eventName = document.createElement("div");
          eventName.textContent = area.eventName;
          eventName.style.cssText = "font-size: 12px; opacity: 0.75; margin-left: 22px; color: #e9ecf1;";

          item.appendChild(content);
          item.appendChild(eventName);

          L.DomEvent.on(item, "click", (e) => {
            L.DomEvent.stopPropagation(e);
            handleSelectArea(area);
          });
          L.DomEvent.on(item, "mousedown", (e) => {
            L.DomEvent.stopPropagation(e);
          });

          item.addEventListener("mouseenter", () => {
            if (!isSelected) {
              item.style.background = "rgba(255,255,255,0.1)";
            } else {
              item.style.background = "rgba(255,255,255,0.2)";
            }
          });
          item.addEventListener("mouseleave", () => {
            if (!isSelected) {
              item.style.background = "transparent";
            } else {
              item.style.background = "rgba(255,255,255,0.15)";
            }
          });

          panel.appendChild(item);
        });
      } else {
        const empty = document.createElement("div");
        empty.textContent = "No impact areas yet.";
        empty.style.cssText = "opacity: 0.75; padding: 8px; color: #e9ecf1;";
        panel.appendChild(empty);
      }

      wrapper.appendChild(panel);
    }

    container.appendChild(wrapper);
  }, [isOpen, sortedAreas, selectedAreaId, hasAreas, onSelectImpactArea]);

  return null;
}
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

  // When true, hide overlay controls (Impact Areas menu); used when layout provides toggles
  hideControls = false,
}) {

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
  // Use impactAreas prop if available (has correct filtered tower count), otherwise compute from towers
  const areasWithTowerCounts = useMemo(() => {
    // If impactAreas prop is provided with towerCount, use it as source of truth
    if (impactAreas && impactAreas.length > 0) {
      // Create a map of impactAreas by id for quick lookup
      const impactAreasMap = new Map(impactAreas.map(ia => [ia.id, ia]));
      
      return affectedAreas.map(area => {
        // Try to get towerCount from impactAreas prop first (has correct filtered count)
        const impactArea = impactAreasMap.get(area.id);
        if (impactArea && impactArea.towerCount != null) {
          return { ...area, towerCount: impactArea.towerCount };
        }
        // Fallback: compute from towers if impactAreas not available
        if (!towers || towers.length === 0) {
          return { ...area, towerCount: 0 };
        }
        const towerCount = countTowersInArea(area, towers);
        return { ...area, towerCount };
      });
    }
    
    // Fallback: compute from towers if impactAreas prop not provided
    if (!towers || towers.length === 0) {
      return affectedAreas.map(area => ({ ...area, towerCount: 0 }));
    }

    return affectedAreas.map(area => {
      const towerCount = countTowersInArea(area, towers);
      return { ...area, towerCount };
    });
  }, [affectedAreas, towers, impactAreas]);

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

  const mapHeight = hideControls ? "100%" : "80vh";

  return (
    <div style={{ height: mapHeight, width: "100%", position: "relative" }}>
      <MapContainer center={center} zoom={zoom} preferCanvas style={{ height: "100%", width: "100%" }}>
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
                    <div style={{ marginTop: 8, fontSize: 11, color: "rgba(0,0,0,0.6)", fontStyle: "italic" }}>
                      See right panel for full details
                    </div>
                  </div>
                </Popup>
              </ZOrderedRectangle>
            );
          })}

        {/* Towers */}
        {layers.towers &&
          towers.map((t, idx) => {
            const towerId = getTowerId ? getTowerId(t) : t.id;
            const kpi = kpiByTowerId[towerId];

            return (
              <CircleMarker
                // Source data has ~200 duplicate ids for genuinely distinct
                // sites (different lat/lon), so key on id+index for uniqueness.
                key={`${t.id}-${idx}`}
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
        {/* Impact Areas Control - always visible on map */}
        <ImpactAreasControl
          impactAreas={impactAreas}
          selectedAreaId={selectedAreaId}
          onSelectImpactArea={onSelectImpactArea}
        />
      </MapContainer>
    </div>
  );
}
