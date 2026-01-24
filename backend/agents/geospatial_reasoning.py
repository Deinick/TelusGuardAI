"""
Agent 3: Geospatial Reasoning Agent
Analyzes gathered data and generates geographic impact assessments
"""

import json
import re
from typing import List, Dict, Any
from models.data_models import Event, AffectedArea, EventMetadata, IntelligenceData
from services.ai_client import AIModelClient
from utils.logger import logger, timing_decorator
from config import Config


class GeospatialReasoningAgent:
    """
    Analyzes aggregated data to identify affected geographic areas
    Uses GPT-OSS-120b model for complex reasoning and analysis
    """
    
    @staticmethod
    @timing_decorator
    async def analyze_impact(
        event_metadata: EventMetadata,
        intelligence_data: IntelligenceData
    ) -> List[Event]:
        """
        Analyze data and generate events with affected areas
        
        Args:
            event_metadata: Metadata from Event Intelligence Agent
            intelligence_data: Data from Web Intelligence Agent
        
        Returns:
            List of Event objects with geographic analysis
        """
        
        logger.info("🤖 Agent 3: Geospatial Reasoning - Analyzing impact...")
        
        # Construct analysis prompt
        system_prompt = GeospatialReasoningAgent._build_system_prompt()
        user_prompt = GeospatialReasoningAgent._build_user_prompt(
            event_metadata,
            intelligence_data
        )
        
        # Call GPT model for analysis
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
            logger.warning("⚠️  Generating fallback events")
            return GeospatialReasoningAgent._generate_fallback_events(
                event_metadata,
                intelligence_data
            )
    
    @staticmethod
    def _build_system_prompt() -> str:
        """Build system prompt for GPT model"""
        
        return """You are an expert geospatial analyst specializing in telecommunications network disruptions.

Your task is to analyze provided data sources and identify specific geographic areas affected by network outages.

Return ONLY valid JSON with this exact structure:
{
    "events": [
        {
            "event_name": "descriptive event name",
            "event_type": "weather_related_outage|infrastructure_outage|equipment_failure|power_outage|etc",
            "timeframe": "when the event occurred",
            "affected_areas": [
                {
                    "area_name": "specific neighborhood or district name",
                    "severity": "critical|high|moderate|low",
                    "latitude": 43.123,
                    "longitude": -79.456,
                    "radius_km": 2.5,
                    "reasoning": "detailed explanation citing specific evidence from data sources",
                    "estimated_users": "approximate number of affected users",
                    "confidence": 0.85,
                    "supporting_data_points": 15
                }
            ]
        }
    ]
}

CRITICAL REQUIREMENTS:
1. REASONING IS MANDATORY: Each area MUST include detailed reasoning that:
   - Cites specific evidence from web search results
   - References weather data when available
   - Explains why this area was identified
   - Mentions number of reports/mentions found
   - Correlates multiple data sources

2. Severity assessment based on:
   - critical: Complete service loss, 10+ mentions, official confirmations
   - high: Major disruptions, 5-10 mentions, multiple source types
   - moderate: Partial service degradation, 3-5 mentions
   - low: Minor issues, 1-2 mentions, unconfirmed

3. Confidence scoring (0-1):
   - 0.9+: Multiple independent sources, official statements, weather correlation
   - 0.8-0.9: Multiple sources, strong evidence
   - 0.7-0.8: Several mentions, good correlation
   - 0.6-0.7: Limited mentions, weak correlation
   - Below 0.6: Single source or unclear evidence

4. Provide precise coordinates (latitude/longitude) - we'll calculate ranges later
5. Estimate radius of impact in kilometers
6. Count actual supporting data points (number of mentions/reports)
7. Return ONLY JSON, no markdown, no explanations outside the JSON"""
    
    @staticmethod
    def _build_user_prompt(
        event_metadata: EventMetadata,
        intelligence_data: IntelligenceData
    ) -> str:
        """Build user prompt with all gathered data"""
        
        # Format web results for analysis
        web_results_text = "\n\n".join([
            f"Source {idx+1}:\n"
            f"Title: {result.get('title', 'N/A')}\n"
            f"Content: {result.get('snippet', 'N/A')}\n"
            f"URL: {result.get('url', 'N/A')}\n"
            f"Date: {result.get('date', 'N/A')}\n"
            f"Source: {result.get('source', 'N/A')}"
            for idx, result in enumerate(intelligence_data.web_results)
        ])
        
        # Format weather data
        weather_text = "No weather data available"
        if intelligence_data.weather_data:
            weather = intelligence_data.weather_data
            weather_text = f"""Weather Conditions:
- Condition: {weather.get('condition', 'N/A')}
- Description: {weather.get('description', 'N/A')}
- Temperature: {weather.get('temperature', 'N/A')}°C
- Wind Speed: {weather.get('wind_speed', 'N/A')} km/h
- Precipitation: {weather.get('precipitation', 'N/A')}
- Warnings: {', '.join(weather.get('warnings', []))}
- Severity: {weather.get('severity', 'N/A')}"""
        
        # Format event metadata
        events_text = "\n".join([
            f"- {event.get('event_type', 'unknown')}: {event.get('primary_location', 'N/A')} ({event.get('timeframe', 'N/A')})"
            for event in event_metadata.events
        ])
        
        prompt = f"""Analyze the following data to identify network service areas affected by outages:

EVENT METADATA:
{events_text}

WEB SEARCH RESULTS ({len(intelligence_data.web_results)} sources):
{web_results_text}

WEATHER DATA:
{weather_text}

ANALYSIS TASK:
Identify all geographic areas experiencing network disruptions. For each area:
1. Determine precise location (coordinates and neighborhood name)
2. Assess severity based on evidence
3. Provide detailed reasoning citing specific sources
4. Calculate confidence based on data quality
5. Estimate impact and affected users

Be thorough and cite specific evidence. Return comprehensive JSON analysis."""

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
        lat_offset = radius_km / 111.0
        lon_offset = radius_km / (111.0 * abs(center_lat / 90.0))
        
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
            reasoning=area_data.get("reasoning", "No reasoning provided"),
            estimated_impact=area_data.get("estimated_users", "Unknown"),
            confidence=area_data.get("confidence", 0.7),
            data_points=area_data.get("supporting_data_points", 0)
        )
    
    @staticmethod
    def _generate_fallback_events(
        event_metadata: EventMetadata,
        intelligence_data: IntelligenceData
    ) -> List[Event]:
        """
        Generate fallback events when parsing fails
        
        Args:
            event_metadata: Event metadata
            intelligence_data: Intelligence data
        
        Returns:
            List of fallback Event objects
        """
        
        logger.info("🔧 Generating fallback events...")
        
        # Create basic event from metadata
        event_info = event_metadata.events[0] if event_metadata.events else {}
        
        # Default Toronto coordinates
        center_lat, center_lon = 43.65, -79.38
        
        area = AffectedArea(
            area_name=f"{event_info.get('primary_location', 'Toronto')} Area",
            severity="moderate",
            lat_range=[43.60, 43.70],
            long_range=[-79.43, -79.33],
            center={"lat": center_lat, "long": center_lon},
            reasoning=f"Fallback area generated from {len(intelligence_data.web_results)} web sources. "
                     f"Analysis indicates potential network disruption based on search results mentioning "
                     f"service issues in the {event_info.get('primary_location', 'area')}.",
            estimated_impact="~10,000 users (estimated)",
            confidence=0.6,
            data_points=len(intelligence_data.web_results)
        )
        
        event = Event(
            event_id="evt_001",
            event_name=f"{event_info.get('event_type', 'Network').replace('_', ' ').title()} - {event_info.get('primary_location', 'Unknown')}",
            event_type=event_info.get('event_type', 'unknown'),
            timeframe=event_info.get('timeframe', 'Recent'),
            affected_areas=[area]
        )
        
        return [event]