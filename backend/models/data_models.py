"""
Data models and enums for Network Impact Analyzer
"""

from dataclasses import dataclass, asdict
from typing import List, Dict, Any
from enum import Enum


class EventType(Enum):
    """Types of network disruption events"""
    WEATHER_RELATED = "weather_related_outage"
    INFRASTRUCTURE = "infrastructure_outage"
    CYBER_ATTACK = "cyber_attack"
    NATURAL_DISASTER = "natural_disaster"
    EQUIPMENT_FAILURE = "equipment_failure"
    POWER_OUTAGE = "power_outage"
    UNKNOWN = "unknown"


class Severity(Enum):
    """Severity levels for network impact"""
    CRITICAL = "critical"
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"


@dataclass
class AffectedArea:
    """
    Represents a geographic area affected by network disruption
    """
    area_name: str
    severity: str
    lat_range: List[float]  # [min_lat, max_lat]
    long_range: List[float]  # [min_long, max_long]
    center: Dict[str, float]  # {"lat": x, "long": y}
    reasoning: str
    estimated_impact: str
    confidence: float
    data_points: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)


@dataclass
class Event:
    """
    Represents a network disruption event
    """
    event_id: str
    event_name: str
    event_type: str
    timeframe: str
    affected_areas: List[AffectedArea]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "event_id": self.event_id,
            "event_name": self.event_name,
            "event_type": self.event_type,
            "timeframe": self.timeframe,
            "affected_areas": [area.to_dict() for area in self.affected_areas]
        }


@dataclass
class AnalysisResult:
    """
    Complete analysis result returned to frontend
    """
    query: str
    timestamp: str
    summary: str
    events: List[Event]
    total_events: int
    total_affected_areas: int
    analysis_metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "query": self.query,
            "timestamp": self.timestamp,
            "summary": self.summary,
            "events": [event.to_dict() for event in self.events],
            "total_events": self.total_events,
            "total_affected_areas": self.total_affected_areas,
            "analysis_metadata": self.analysis_metadata
        }


@dataclass
class EventMetadata:
    """
    Metadata extracted from user query by Event Intelligence Agent
    """
    events: List[Dict[str, Any]]
    search_queries: List[str]
    requires_weather_data: bool
    geographic_scope: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class IntelligenceData:
    """
    Data gathered by Web Intelligence Agent
    """
    web_results: List[Dict[str, str]]
    weather_data: Dict[str, Any]
    total_data_points: int
    search_queries_used: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)