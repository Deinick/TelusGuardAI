"""
Main orchestrator coordinating all agents
"""

import time
from datetime import datetime
from typing import Dict, Any, List
from agents.event_intelligence import EventIntelligenceAgent
from agents.web_intelligence import WebIntelligenceAgent
from agents.geospatial_reasoning import GeospatialReasoningAgent
from models.data_models import AnalysisResult, Event
from utils.logger import logger, timing_decorator
from utils.cache import cache
from config import Config


class NetworkImpactOrchestrator:
    """
    Main orchestration class that coordinates all agents
    to analyze network impact from user queries
    """
    
    @staticmethod
    @timing_decorator
    async def analyze(
        question: str,
        options: Dict[str, Any] = None
    ) -> AnalysisResult:
        """
        Main orchestration workflow
        
        Workflow:
        1. Event Intelligence Agent parses the question
        2. Web Intelligence Agent gathers data
        3. Geospatial Reasoning Agent analyzes impact
        4. Results are filtered and formatted
        
        Args:
            question: User's natural language question
            options: Optional parameters:
                - max_areas: Maximum areas to return (default: 10)
                - min_confidence: Minimum confidence threshold (default: 0.65)
                - include_reasoning: Include detailed reasoning (default: True)
        
        Returns:
            AnalysisResult object with complete analysis
        """
        
        logger.info("=" * 80)
        logger.info("🚀 NETWORK IMPACT ANALYSIS STARTING")
        logger.info("=" * 80)
        logger.info(f"📝 Query: '{question}'")
        
        start_time = time.time()
        options = options or {}
        
        # ====================================================================
        # STEP 0: Check Cache
        # ====================================================================
        
        cache_key = f"analysis_{question}"
        cached_result = cache.get(cache_key)
        if cached_result:
            logger.info("✨ Returning cached result")
            return cached_result
        
        # ====================================================================
        # STEP 1: Event Intelligence Agent
        # ====================================================================
        
        logger.info("\n" + "─" * 80)
        logger.info("STEP 1: Event Intelligence")
        logger.info("─" * 80)
        
        event_metadata = await EventIntelligenceAgent.analyze_query(question)
        
        # ====================================================================
        # STEP 2: Web Intelligence Agent
        # ====================================================================
        
        logger.info("\n" + "─" * 80)
        logger.info("STEP 2: Web Intelligence")
        logger.info("─" * 80)
        
        intelligence_data = await WebIntelligenceAgent.gather_intelligence(
            event_metadata
        )
        
        # ====================================================================
        # STEP 3: Geospatial Reasoning Agent
        # ====================================================================
        
        logger.info("\n" + "─" * 80)
        logger.info("STEP 3: Geospatial Reasoning")
        logger.info("─" * 80)
        
        events = await GeospatialReasoningAgent.analyze_impact(
            event_metadata,
            intelligence_data
        )
        
        # ====================================================================
        # STEP 4: Post-Processing
        # ====================================================================
        
        logger.info("\n" + "─" * 80)
        logger.info("STEP 4: Post-Processing")
        logger.info("─" * 80)
        
        # Apply filters
        max_areas = options.get("max_areas", Config.MAX_AREAS_RETURNED)
        min_confidence = options.get("min_confidence", Config.MIN_CONFIDENCE_THRESHOLD)
        
        events = NetworkImpactOrchestrator._filter_events(
            events,
            max_areas=max_areas,
            min_confidence=min_confidence
        )
        
        # Remove reasoning if not requested
        if not options.get("include_reasoning", True):
            events = NetworkImpactOrchestrator._remove_reasoning(events)
        
        # ====================================================================
        # STEP 5: Generate Summary
        # ====================================================================
        
        total_areas = sum(len(e.affected_areas) for e in events)
        summary = NetworkImpactOrchestrator._generate_summary(events, total_areas)
        
        # ====================================================================
        # STEP 6: Build Result
        # ====================================================================
        
        analysis_duration_ms = int((time.time() - start_time) * 1000)
        
        result = AnalysisResult(
            query=question,
            timestamp=datetime.now().isoformat(),
            summary=summary,
            events=events,
            total_events=len(events),
            total_affected_areas=total_areas,
            analysis_metadata={
                "web_searches_performed": len(intelligence_data.search_queries_used),
                "weather_api_calls": 1 if intelligence_data.weather_data else 0,
                "total_data_points_analyzed": intelligence_data.total_data_points,
                "analysis_duration_ms": analysis_duration_ms,
                "data_sources": [
                    "web_search",
                    "openweathermap"
                ] if intelligence_data.weather_data else ["web_search"],
                "search_queries_used": intelligence_data.search_queries_used,
                "filters_applied": {
                    "max_areas": max_areas,
                    "min_confidence": min_confidence
                }
            }
        )
        
        # Cache result
        cache.set(cache_key, result)
        
        # ====================================================================
        # Done!
        # ====================================================================
        
        logger.info("\n" + "=" * 80)
        logger.info("✨ ANALYSIS COMPLETE")
        logger.info("=" * 80)
        logger.info(f"📊 Results: {len(events)} events, {total_areas} affected areas")
        logger.info(f"⏱️  Total duration: {analysis_duration_ms}ms")
        logger.info("=" * 80 + "\n")
        
        return result
    
    @staticmethod
    def _filter_events(
        events: List[Event],
        max_areas: int,
        min_confidence: float
    ) -> List[Event]:
        """
        Filter events based on criteria
        
        Args:
            events: List of events to filter
            max_areas: Maximum areas per event
            min_confidence: Minimum confidence threshold
        
        Returns:
            Filtered list of events
        """
        
        logger.info(f"🔍 Applying filters: max_areas={max_areas}, min_confidence={min_confidence}")
        
        filtered_events = []
        
        for event in events:
            # Filter areas by confidence
            filtered_areas = [
                area for area in event.affected_areas
                if area.confidence >= min_confidence
            ]
            
            # Sort by confidence (descending)
            filtered_areas.sort(key=lambda a: a.confidence, reverse=True)
            
            # Limit number of areas
            filtered_areas = filtered_areas[:max_areas]
            
            # Only include event if it has areas left
            if filtered_areas:
                event.affected_areas = filtered_areas
                filtered_events.append(event)
        
        areas_before = sum(len(e.affected_areas) for e in events)
        areas_after = sum(len(e.affected_areas) for e in filtered_events)
        
        logger.info(f"✂️  Filtered: {areas_before} → {areas_after} areas")
        
        return filtered_events
    
    @staticmethod
    def _remove_reasoning(events: List[Event]) -> List[Event]:
        """
        Remove detailed reasoning from areas (for compact output)
        
        Args:
            events: List of events
        
        Returns:
            Events with reasoning removed
        """
        
        for event in events:
            for area in event.affected_areas:
                area.reasoning = "Reasoning omitted (set include_reasoning=true to see details)"
        
        return events
    
    @staticmethod
    def _generate_summary(events: List[Event], total_areas: int) -> str:
        """
        Generate human-readable summary of analysis
        
        Args:
            events: List of analyzed events
            total_areas: Total number of affected areas
        
        Returns:
            Summary string
        """
        
        if not events:
            return "No significant network impacts detected based on available data. " \
                   "This could indicate either no current outages or insufficient data sources."
        
        # Build summary components
        event_names = [e.event_name for e in events[:3]]  # First 3 events
        
        summary = f"Analysis identified {len(events)} distinct event(s) affecting {total_areas} area(s). "
        
        if len(events) == 1:
            summary += f"Primary event: {event_names[0]}. "
        else:
            summary += f"Events detected: {', '.join(event_names)}. "
        
        # Add severity context
        severity_counts = {
            "critical": 0,
            "high": 0,
            "moderate": 0,
            "low": 0
        }
        
        for event in events:
            for area in event.affected_areas:
                severity = area.severity.lower()
                if severity in severity_counts:
                    severity_counts[severity] += 1
        
        if severity_counts["critical"] > 0:
            summary += f"{severity_counts['critical']} area(s) experiencing critical service disruption. "
        elif severity_counts["high"] > 0:
            summary += f"{severity_counts['high']} area(s) experiencing high-severity impact. "
        else:
            summary += "Impact levels range from moderate to low. "
        
        # Add confidence note
        avg_confidence = sum(
            area.confidence
            for event in events
            for area in event.affected_areas
        ) / total_areas if total_areas > 0 else 0
        
        if avg_confidence >= 0.8:
            summary += "Analysis confidence: High."
        elif avg_confidence >= 0.7:
            summary += "Analysis confidence: Moderate."
        else:
            summary += "Analysis confidence: Limited data available."
        
        return summary
    
    @staticmethod
    def validate_question(question: str) -> tuple[bool, str]:
        """
        Validate user question before processing
        
        Args:
            question: User's question
        
        Returns:
            (is_valid, error_message) tuple
        """
        
        if not question or not question.strip():
            return False, "Question cannot be empty"
        
        if len(question) < 10:
            return False, "Question too short (minimum 10 characters)"
        
        if len(question) > 500:
            return False, "Question too long (maximum 500 characters)"
        
        return True, ""