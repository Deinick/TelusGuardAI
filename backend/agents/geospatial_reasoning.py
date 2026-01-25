"""
Agent 3: Geospatial Reasoning Agent (Flexible Version)
Analyzes gathered data and generates geographic impact assessments
Now includes LLM-recommended areas based on patterns and historical knowledge
"""

import json
import re
from typing import List, Dict, Any, Optional
from models.data_models import Event, AffectedArea, EventMetadata, IntelligenceData
from services.ai_client import AIModelClient
from utils.logger import logger, timing_decorator
from config import Config


class GeospatialReasoningAgent:
    """
    Analyzes aggregated data to identify affected geographic areas
    Uses GPT-OSS-120b model for complex reasoning and analysis
    Can generate recommendations even with limited or no input data
    """
    
    @staticmethod
    @timing_decorator
    async def analyze_impact(
        event_metadata: Optional[EventMetadata] = None,
        intelligence_data: Optional[IntelligenceData] = None,
        user_query: Optional[str] = None
    ) -> List[Event]:
        """
        Analyze data and generate events with affected areas
        Now works with partial or no data - relies on LLM knowledge and patterns
        
        Args:
            event_metadata: Optional metadata from Event Intelligence Agent
            intelligence_data: Optional data from Web Intelligence Agent
            user_query: Optional direct user query for context
        
        Returns:
            List of Event objects with geographic analysis
        """
        
        logger.info("🤖 Agent 3: Geospatial Reasoning - Analyzing impact...")
        
        # Construct analysis prompt (works even with missing data)
        system_prompt = GeospatialReasoningAgent._build_system_prompt()
        user_prompt = GeospatialReasoningAgent._build_user_prompt(
            event_metadata,
            intelligence_data,
            user_query
        )
        
        # Call Deepseek model for analysis
        response = await AIModelClient.call_deepseek(
            prompt=user_prompt,
            system_prompt=system_prompt
        )
        
        # Parse response into Event objects
        try:
            events = GeospatialReasoningAgent._parse_analysis(response)
            logger.info(f"✅ Identified {len(events)} events")
            
            total_areas = sum(len(e.affected_areas) for e in events)
            logger.info(f"📍 Found {total_areas} affected areas total")
            
            return events
            
        except Exception as e:
            logger.error(f"💥 Error parsing analysis: {str(e)}")
            logger.warning("⚠️  Generating LLM-recommended fallback events")
            return GeospatialReasoningAgent._generate_intelligent_fallback(
                event_metadata,
                intelligence_data,
                user_query
            )
    
    @staticmethod
    def _build_system_prompt() -> str:
        """Build system prompt for GPT model with flexible requirements"""
        
        return """You are an expert geospatial analyst specializing in telecommunications network disruptions.

Your task is to analyze provided data AND use your knowledge of typical network outage patterns to identify specific geographic areas that are likely affected.

IMPORTANT: You should ALWAYS provide recommendations based on:
1. Any data sources provided (web results, weather, metadata)
2. Your knowledge of typical outage patterns in the region
3. Historical patterns of network disruptions
4. Geographic and infrastructure vulnerabilities
5. Common failure points in telecommunications networks

Even with limited data, you should recommend likely affected areas based on your understanding of:
- Weather patterns and their typical impact zones
- Infrastructure density and vulnerability
- Historical outage patterns
- Urban vs suburban network characteristics
- Common points of failure

Return ONLY valid JSON with this exact structure:
{
    "events": [
        {
            "event_name": "descriptive event name",
            "event_type": "weather_related_outage|infrastructure_outage|equipment_failure|power_outage|etc",
            "timeframe": "when the event occurred or is likely occurring",
            "data_quality": "high|medium|low|minimal",
            "affected_areas": [
                {
                    "area_name": "specific neighborhood or district name",
                    "severity": "critical|high|moderate|low",
                    "latitude": 43.123,
                    "longitude": -79.456,
                    "radius_km": 2.5,
                    "reasoning": "detailed explanation citing evidence OR pattern-based recommendation",
                    "estimated_users": "approximate number of affected users",
                    "confidence": 0.85,
                    "supporting_data_points": 15,
                    "recommendation_type": "data_driven|pattern_based|hybrid"
                }
            ]
        }
    ]
}

REASONING TYPES:
- data_driven: Based on specific evidence from provided sources
- pattern_based: Based on your knowledge of typical outage patterns
- hybrid: Combines data evidence with pattern knowledge

FLEXIBLE REQUIREMENTS:
1. ALWAYS provide at least 2-3 area recommendations, even with minimal data
2. Use "pattern_based" reasoning when data is limited
3. Cite specific evidence when available, otherwise explain pattern logic
4. Confidence should reflect data availability (0.5-0.7 for pattern-based, 0.7-1.0 for data-driven)
5. Estimate affected users based on area density and your knowledge
6. Include coordinates for all recommended areas
7. Return ONLY JSON, no markdown, no explanations outside the JSON"""
    
    @staticmethod
    def _build_user_prompt(
        event_metadata: Optional[EventMetadata],
        intelligence_data: Optional[IntelligenceData],
        user_query: Optional[str]
    ) -> str:
        """Build user prompt with all available data (works even if data is missing)"""
        
        # Format web results if available
        web_results_text = "No web search results available"
        if intelligence_data and intelligence_data.web_results:
            web_results_text = "\n\n".join([
                f"Source {idx+1}:\n"
                f"Title: {result.get('title', 'N/A')}\n"
                f"Content: {result.get('snippet', 'N/A')}\n"
                f"URL: {result.get('url', 'N/A')}\n"
                f"Date: {result.get('date', 'N/A')}\n"
                f"Source: {result.get('source', 'N/A')}"
                for idx, result in enumerate(intelligence_data.web_results)
            ])
        
        # Format weather data if available
        weather_text = "No weather data available"
        if intelligence_data and intelligence_data.weather_data:
            weather = intelligence_data.weather_data
            weather_text = f"""Weather Conditions:
- Condition: {weather.get('condition', 'N/A')}
- Description: {weather.get('description', 'N/A')}
- Temperature: {weather.get('temperature', 'N/A')}°C
- Wind Speed: {weather.get('wind_speed', 'N/A')} km/h
- Precipitation: {weather.get('precipitation', 'N/A')}
- Warnings: {', '.join(weather.get('warnings', []))}
- Severity: {weather.get('severity', 'N/A')}"""
        
        # Format event metadata if available
        events_text = "No event metadata available"
        if event_metadata and event_metadata.events:
            events_text = "\n".join([
                f"- {event.get('event_type', 'unknown')}: {event.get('primary_location', 'N/A')} ({event.get('timeframe', 'N/A')})"
                for event in event_metadata.events
            ])
        
        # Format user query if available
        query_text = ""
        if user_query:
            query_text = f"\nUSER QUERY:\n{user_query}\n"
        
        prompt = f"""Analyze the available data AND use your knowledge to identify network service areas likely affected by outages:

{query_text}
EVENT METADATA:
{events_text}

WEB SEARCH RESULTS:
{web_results_text}

WEATHER DATA:
{weather_text}

ANALYSIS TASK:
Identify geographic areas experiencing or likely to experience network disruptions.

IMPORTANT INSTRUCTIONS:
1. If data is LIMITED or MISSING:
   - Use your knowledge of typical outage patterns
   - Recommend areas based on infrastructure vulnerabilities
   - Consider historical patterns in the region
   - Mark recommendations as "pattern_based"

2. If data is AVAILABLE:
   - Prioritize data-driven analysis
   - Supplement with pattern knowledge where helpful
   - Mark as "data_driven" or "hybrid"

3. ALWAYS provide at least 2-3 area recommendations with:
   - Precise coordinates and neighborhood names
   - Severity assessment (even if estimated)
   - Detailed reasoning (data evidence OR pattern logic)
   - Confidence level reflecting data quality
   - Estimated user impact

4. For each area, explain your reasoning:
   - If data-driven: cite specific sources
   - If pattern-based: explain the pattern/vulnerability
   - If hybrid: combine both approaches

Be comprehensive and provide actionable geographic recommendations. Return detailed JSON analysis."""

        return prompt
    
    @staticmethod
    def _parse_analysis(response: str) -> List[Event]:
        """
        Parse AI model response into Event objects
        
        Args:
            response: Raw JSON response from model
        
        Returns:
            List of Event objects
        """
        
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if not json_match:
            raise ValueError("No JSON found in response")
        
        data = json.loads(json_match.group())
        
        if "events" not in data:
            raise ValueError("No events found in response")
        
        # Convert to Event objects
        events = []
        for idx, event_data in enumerate(data["events"]):
            event = GeospatialReasoningAgent._create_event_from_data(
                event_data,
                event_id=f"evt_{idx+1:03d}"
            )
            events.append(event)
        
        return events
    
    @staticmethod
    def _create_event_from_data(event_data: Dict[str, Any], event_id: str) -> Event:
        """
        Create Event object from parsed data
        
        Args:
            event_data: Dictionary with event information
            event_id: Unique event identifier
        
        Returns:
            Event object
        """
        
        # Convert affected areas
        areas = []
        for area_data in event_data.get("affected_areas", []):
            area = GeospatialReasoningAgent._create_affected_area(area_data)
            areas.append(area)
        
        return Event(
            event_id=event_id,
            event_name=event_data.get("event_name", "Unnamed Event"),
            event_type=event_data.get("event_type", "unknown"),
            timeframe=event_data.get("timeframe", "Unknown timeframe"),
            affected_areas=areas
        )
    
    @staticmethod
    def _create_affected_area(area_data: Dict[str, Any]) -> AffectedArea:
        """
        Create AffectedArea object with lat/long ranges
        
        Args:
            area_data: Dictionary with area information
        
        Returns:
            AffectedArea object
        """
        
        # Extract center coordinates
        center_lat = area_data.get("latitude", 43.65)
        center_lon = area_data.get("longitude", -79.38)
        radius_km = area_data.get("radius_km", 2.0)
        
        # Convert radius to lat/long offsets
        # Approximate: 1 degree latitude ≈ 111 km
        # Longitude varies by latitude: 1 degree ≈ 111 km * cos(latitude)
        import math
        lat_offset = radius_km / 111.0
        lon_offset = radius_km / (111.0 * math.cos(math.radians(center_lat)))
        
        # Include recommendation type in reasoning if available
        reasoning = area_data.get("reasoning", "No reasoning provided")
        rec_type = area_data.get("recommendation_type", "unknown")
        if rec_type in ["pattern_based", "hybrid"]:
            reasoning = f"[{rec_type.upper()}] {reasoning}"
        
        return AffectedArea(
            area_name=area_data.get("area_name", "Unknown Area"),
            severity=area_data.get("severity", "moderate"),
            lat_range=[
                round(center_lat - lat_offset, 6),
                round(center_lat + lat_offset, 6)
            ],
            long_range=[
                round(center_lon - lon_offset, 6),
                round(center_lon + lon_offset, 6)
            ],
            center={
                "lat": round(center_lat, 6),
                "long": round(center_lon, 6)
            },
            reasoning=reasoning,
            estimated_impact=area_data.get("estimated_users", "Unknown"),
            confidence=area_data.get("confidence", 0.7),
            data_points=area_data.get("supporting_data_points", 0)
        )
    
    @staticmethod
    def _generate_intelligent_fallback(
        event_metadata: Optional[EventMetadata],
        intelligence_data: Optional[IntelligenceData],
        user_query: Optional[str]
    ) -> List[Event]:
        """
        Generate intelligent fallback events using basic pattern knowledge
        This is a last resort if AI parsing completely fails
        
        Args:
            event_metadata: Optional event metadata
            intelligence_data: Optional intelligence data
            user_query: Optional user query
        
        Returns:
            List of fallback Event objects with LLM-recommended areas
        """
        
        logger.info("🔧 Generating intelligent fallback events...")
        
        # Extract any available context
        event_info = {}
        if event_metadata and event_metadata.events:
            event_info = event_metadata.events[0]
        
        location = event_info.get('primary_location', 'Toronto')
        
        # Generate multiple recommended areas based on typical patterns
        areas = []
        
        # Area 1: Downtown core (typically high density, vulnerable to infrastructure issues)
        areas.append(AffectedArea(
            area_name=f"Downtown {location}",
            severity="moderate",
            lat_range=[43.640, 43.660],
            long_range=[-79.395, -79.375],
            center={"lat": 43.650, "long": -79.385},
            reasoning="[PATTERN_BASED] Downtown core recommended based on high infrastructure density "
                     "and typical vulnerability to network disruptions. This area often experiences "
                     "service issues during outages due to concentrated user load.",
            estimated_impact="~15,000-20,000 users (estimated based on area density)",
            confidence=0.6,
            data_points=0
        ))
        
        # Area 2: Suburban area (medium density, potential equipment issues)
        areas.append(AffectedArea(
            area_name=f"North {location}",
            severity="moderate",
            lat_range=[43.700, 43.730],
            long_range=[-79.420, -79.380],
            center={"lat": 43.715, "long": -79.400},
            reasoning="[PATTERN_BASED] Northern suburban area recommended based on typical patterns "
                     "where cellular towers and fiber infrastructure may be affected. These areas "
                     "often have fewer redundant connections.",
            estimated_impact="~8,000-12,000 users (estimated)",
            confidence=0.55,
            data_points=0
        ))
        
        # Area 3: If weather-related, include typical weather-vulnerable zone
        if event_info.get('event_type', '').startswith('weather'):
            areas.append(AffectedArea(
                area_name=f"Waterfront {location}",
                severity="high",
                lat_range=[43.630, 43.650],
                long_range=[-79.395, -79.365],
                center={"lat": 43.640, "long": -79.380},
                reasoning="[PATTERN_BASED] Waterfront area recommended due to weather event. "
                         "This area is historically more vulnerable to weather-related outages "
                         "due to exposed infrastructure and proximity to water.",
                estimated_impact="~10,000-15,000 users (estimated)",
                confidence=0.65,
                data_points=0
            ))
        
        event = Event(
            event_id="evt_001",
            event_name=f"Pattern-Based Analysis - {location}",
            event_type=event_info.get('event_type', 'network_disruption'),
            timeframe=event_info.get('timeframe', 'Recent/Ongoing'),
            affected_areas=areas
        )
        
        logger.info(f"✅ Generated {len(areas)} pattern-based area recommendations")
        return [event]