import time 
from typing import Dict, Any, Optional

class IncidentEngine: 
    """
    Manages temporary incidents affecting towers.
    Incidents automatically expire after duration_seconds
    """

    def __init__(self):
        # tower_id -> incident dict 
        self.active: Dict[str, Dict[str, Any]] = {}

    def _now(self) -> float: 
        return time.time()
    
    def _set_incident(self, tower_id: str, incident: Dict[str, Any]) -> None: 
        incident["start_time"] = self._now()
        self.active[tower_id] = incident

    def traffic_surge(self, tower_id: str, multiplier: float = 2.0, duration_seconds: int = 15) -> None:
        """
        Makes a tower suddenly overloaded.
        This should push latency + loss up and trigger congestion detection
        """

        self._set_incident(tower_id, {
            "type": "TRAFFIC_SURGE", 
            "multiplier": multiplier,
            "duration_seconds": duration_seconds
        })

    def tower_outage(self, tower_id: str, duration_seconds: int = 15) -> None:
        """
        Simulates tower down: traffic becomes almost zero and loss becomes huge.
        """
        self._set_incident(tower_id, {
            "type": "OUTAGE", 
            "duration_seconds": duration_seconds
        })

    def loss_spike(self, tower_id: str, extra_loss_pct: float = 8.0, duration_seconds: int = 12) -> None:
        """
        Simulates sudden degradation: adds packet loss without changing traffic much
        """
        self._set_incident(tower_id, {
            "type": "LOSS_SPIKE",
            "extra_loss_pct": extra_loss_pct,
            "duration_seconds": duration_seconds
        })

    def get_incident(self, tower_id: str) -> Optional[Dict[str, Any]]:
        """
        Returns active incident if not expired; otherwise None.
        """
        inc = self.active.get(tower_id)
        if not inc:
            return None

        elapsed = self._now() - inc["start_time"]
        if elapsed > inc["duration_seconds"]:
            # expired
            del self.active[tower_id]
            return None

        return inc
