// Bundled sample scenario used by demo mode (no backend) and as the
// DashboardPage's default view before any analysis has run.
export const MOCK_AGENT_RESPONSE = {
  events: [
    {
      event_id: "event_bc_place",
      event_name: "Concert at BC Place",
      affected_areas: [
        {
          area_name: "BC Place / Stadium District",
          center: { latitude: 49.2767, longitude: -123.1119 },
          lat_range: [49.2725, 49.281],
          long_range: [-123.118, -123.105],
          severity: "critical",
          confidence: 0.82,
          estimated_impact: "~12,000 users",
          reasoning: "High event intensity near the stadium combined with elevated baseline traffic on nearby towers.",
          affected_towers: ["T_102", "T_087", "T_144"],
          mitigation_actions: ["load-balance to adjacent towers", "reserve simulated capacity for peak window"],
        },
      ],
    },
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
          affected_towers: ["T_A", "T_B", "T_C"],
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
          affected_towers: ["T_1", "T_2", "T_3"],
        },
      ],
    },
  ],
};
