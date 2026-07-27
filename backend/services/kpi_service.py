"""
KPI Service for Tower Performance Metrics

Maintains per-tower KPI state with deterministic simulation and smoothing.
"""

import random
import time
from typing import Dict, Optional
from datetime import datetime


class KPIService:
    """
    Service that maintains and updates KPI state for towers.
    Uses deterministic randomness with smoothing for stable values.
    """
    
    def __init__(self, seed: int = 42):
        """
        Initialize KPI service with a seed for deterministic randomness.
        
        Args:
            seed: Random seed for deterministic behavior
        """
        self.seed = seed
        self.rng = random.Random(seed)
        
        # Per-tower KPI state: tower_id -> {
        #   "traffic": float 0..1,
        #   "latency_ms": int,
        #   "packet_loss": float 0..0.2,
        #   "energy": float 0..1,
        #   "status": "ok"|"degraded"|"down",
        #   "last_update": float (timestamp)
        # }
        self.kpi_state: Dict[str, Dict] = {}
        
        # Per-tower random generators (for deterministic per-tower behavior)
        self.tower_rngs: Dict[str, random.Random] = {}
        
        # Smoothing factor (0.0 = no smoothing, 1.0 = no change)
        self.smoothing = 0.7
        
        # Base update interval (seconds)
        self.update_interval = 1.0
        self.last_global_update = time.time()
    
    def _get_tower_rng(self, tower_id: str) -> random.Random:
        """Get or create a deterministic RNG for a specific tower."""
        if tower_id not in self.tower_rngs:
            # Create deterministic seed from tower_id
            tower_seed = hash(tower_id) % (2**31)
            self.tower_rngs[tower_id] = random.Random(tower_seed)
        return self.tower_rngs[tower_id]
    
    def _initialize_tower_kpi(self, tower_id: str) -> Dict:
        """Initialize KPI values for a new tower."""
        rng = self._get_tower_rng(tower_id)
        
        return {
            "traffic": rng.uniform(0.2, 0.7),
            "latency_ms": int(rng.uniform(20, 60)),
            "packet_loss": rng.uniform(0.0, 0.05),
            "energy": rng.uniform(0.3, 0.8),
            "status": "ok",
            "last_update": time.time()
        }
    
    def _update_tower_kpi(self, tower_id: str) -> Dict:
        """
        Update KPI for a single tower with smoothing.
        Returns updated KPI dict.
        """
        rng = self._get_tower_rng(tower_id)
        
        # Get current state or initialize
        current = self.kpi_state.get(tower_id)
        if not current:
            current = self._initialize_tower_kpi(tower_id)
            self.kpi_state[tower_id] = current
        
        # Generate new target values
        new_traffic = rng.uniform(0.1, 0.9)
        new_latency = int(rng.uniform(15, 100))
        new_loss = rng.uniform(0.0, 0.15)
        new_energy = rng.uniform(0.2, 0.9)
        
        # Smooth: blend old and new
        traffic = current["traffic"] * self.smoothing + new_traffic * (1 - self.smoothing)
        latency_ms = int(current["latency_ms"] * self.smoothing + new_latency * (1 - self.smoothing))
        packet_loss = current["packet_loss"] * self.smoothing + new_loss * (1 - self.smoothing)
        energy = current["energy"] * self.smoothing + new_energy * (1 - self.smoothing)
        
        # Clamp values
        traffic = max(0.0, min(1.0, traffic))
        packet_loss = max(0.0, min(0.2, packet_loss))
        energy = max(0.0, min(1.0, energy))
        latency_ms = max(10, min(200, latency_ms))
        
        # Determine status based on thresholds
        if latency_ms > 100 or packet_loss > 0.1 or traffic > 0.95:
            status = "down"
        elif latency_ms > 70 or packet_loss > 0.05 or traffic > 0.85:
            status = "degraded"
        else:
            status = "ok"
        
        # Update state
        updated = {
            "traffic": round(traffic, 3),
            "latency_ms": latency_ms,
            "packet_loss": round(packet_loss, 4),
            "energy": round(energy, 3),
            "status": status,
            "last_update": time.time()
        }
        
        self.kpi_state[tower_id] = updated
        return updated
    
    def get_kpis(self, tower_ids: list[str]) -> Dict[str, Dict]:
        """
        Get KPIs for specified tower IDs.
        Updates KPIs if needed (based on update interval).
        
        Args:
            tower_ids: List of tower IDs to get KPIs for
            
        Returns:
            Dict mapping tower_id -> KPI dict
        """
        now = time.time()
        
        # Update towers that need updating
        for tower_id in tower_ids:
            current = self.kpi_state.get(tower_id)
            if not current or (now - current["last_update"]) >= self.update_interval:
                self._update_tower_kpi(tower_id)
        
        # Return KPIs for requested towers
        result = {}
        for tower_id in tower_ids:
            kpi = self.kpi_state.get(tower_id)
            if kpi:
                # Return a copy without internal fields
                result[tower_id] = {
                    "traffic": kpi["traffic"],
                    "latency_ms": kpi["latency_ms"],
                    "packet_loss": kpi["packet_loss"],
                    "energy": kpi["energy"],
                    "status": kpi["status"]
                }
            else:
                # Initialize if missing
                new_kpi = self._initialize_tower_kpi(tower_id)
                self.kpi_state[tower_id] = new_kpi
                result[tower_id] = {
                    "traffic": new_kpi["traffic"],
                    "latency_ms": new_kpi["latency_ms"],
                    "packet_loss": new_kpi["packet_loss"],
                    "energy": new_kpi["energy"],
                    "status": new_kpi["status"]
                }
        
        return result
    
    def add_incident(self, tower_ids: list[str], incident_type: str = "degraded", duration_seconds: float = 60.0):
        """
        Apply an incident to specified towers (optional feature).
        
        Args:
            tower_ids: List of tower IDs to affect
            incident_type: "degraded" or "down"
            duration_seconds: How long the incident lasts
        """
        # This is a placeholder for incident functionality
        # For now, we'll let the natural simulation handle status changes
        pass


# Global KPI service instance
_kpi_service: Optional[KPIService] = None


def get_kpi_service() -> KPIService:
    """Get or create the global KPI service instance."""
    global _kpi_service
    if _kpi_service is None:
        _kpi_service = KPIService(seed=42)
    return _kpi_service
