import random
from typing import Dict, Any, List


def assign_tower_profiles(towers: List[Dict[str, Any]], seed: int = 42) -> Dict[str, Dict[str, Any]]:
    """
    Assign each tower a weight + capacity so each behaves slightly differently.
    Returns dict: tower_id -> profile
    """
    random.seed(seed)
    profiles: Dict[str, Dict[str, Any]] = {}

    for t in towers:
        tid = t["id"]
        radio = t.get("radio", "LTE")

        base_capacity = {
            "LTE": 950,
            "UMTS": 700,
            "GSM": 550
        }.get(radio, 800)

        weight = random.uniform(0.7, 1.3)

        profiles[tid] = {
            "weight": weight,
            "capacity": base_capacity,
            "lat": t["lat"],
            "lon": t["lon"],
            "radio": radio
        }

    return profiles


def generate_kpis_for_towers(
    baseline_internet: float,
    tower_profiles: Dict[str, Dict[str, Any]],
    incident_engine=None
) -> Dict[str, Dict[str, Any]]:
    """
    Convert baseline internet value -> per-tower KPIs
    Output: tower_id -> KPI dict
    """
    out: Dict[str, Dict[str, Any]] = {}

    for tid, p in tower_profiles.items():
        weight = p["weight"]
        capacity = p["capacity"]

        # 1) Traffic per tower
        traffic = baseline_internet * weight

        # Incident effects (optional)
        incident = incident_engine.get_incident(tid) if incident_engine else None

        if incident:
            if incident["type"] == "TRAFFIC_SURGE":
                traffic *= incident["multiplier"]

            elif incident["type"] == "OUTAGE":
                traffic = 0.5  # near zero

            elif incident["type"] == "LOSS_SPIKE":
                pass

        # 2) Utilization
        util = traffic / max(1.0, capacity)

        # 3) Latency grows nonlinearly when utilization > ~0.7
        latency_ms = 20 + 30 * util + (120 * max(0.0, util - 0.7) ** 2)

        # 4) Packet loss stays tiny until latency is bad
        if latency_ms < 60:
            loss_pct = 0.2
        else:
            loss_pct = 0.2 + (latency_ms - 60) * 0.08

        loss_pct = min(loss_pct, 15.0)

        # Apply incident loss overrides
        if incident:
            if incident["type"] == "OUTAGE":
                loss_pct = 15.0
                latency_ms = max(latency_ms, 150.0)
            elif incident["type"] == "LOSS_SPIKE":
                loss_pct = min(15.0, loss_pct + incident["extra_loss_pct"])

        # 5) Users estimate
        users = int(50 + traffic * 0.4)

        # 6) Energy usage increases with utilization
        energy_kw = 2.0 + 4.0 * min(util, 1.2)

        out[tid] = {
            "traffic": round(traffic, 2),
            "latency_ms": round(latency_ms, 2),
            "packet_loss_pct": round(loss_pct, 2),
            "energy_kw": round(energy_kw, 2),
            "users": users,
            "utilization": round(util, 3),
            "lat": p["lat"],
            "lon": p["lon"],
            "radio": p["radio"],
        }

    return out
