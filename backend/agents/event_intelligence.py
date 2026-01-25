"""
Agent 1: Event Intelligence Agent
Parses user questions and extracts structured event metadata
"""

import json
import re
from typing import Dict, Any
from services.ai_client import AIModelClient
from models.data_models import EventMetadata
from utils.logger import logger, timing_decorator
from config import Config


class EventIntelligenceAgent:
    """
    Analyzes user queries to extract structured event information
    Uses Gemma-3-27b model for natural language understanding
    """
    
    @staticmethod
    @timing_decorator
    async def analyze_query(question: str) -> EventMetadata:
        """
        Parse user question and extract event metadata
        
        Args:
            question: Natural language question from user
        
        Returns:
            EventMetadata object with structured information
        """
        
        logger.info("🤖 Agent 1: Event Intelligence - Starting analysis...")
        logger.info(f"📝 Query: '{question}'")
        
        # Construct system prompt for the model
        system_prompt = """You are an expert at analyzing network outage queries and extracting structured information.

Your task is to parse the user's question and extract:
1. Event types (weather, infrastructure failure, cyber attack, etc.)
2. Geographic locations mentioned
3. Timeframes (when the event occurred)
4. Keywords for effective web searching

Do NOT include:
- Carrier outage pages (Telus, Rogers, Bell)
- User-generated outage maps (Downdetector, Outage.Report, NetStats)
- Forums or social media complaints (Reddit, X, etc.)
- Any links that only report outages without context

Return ONLY valid JSON in this exact format:
{
    "events": [
        {
            "event_type": "weather_related_outage|infrastructure_outage|equipment_failure|cyber_attack|natural_disaster|power_outage|unknown",
            "primary_location": "specific city or region name",
            "timeframe": "when the event occurred (e.g., 'yesterday', 'January 23', 'last week')",
            "keywords": ["list", "of", "relevant", "search", "keywords"]
        }
    ],
    "search_queries": [
        "optimized search query 1",
        "optimized search query 2",
        "optimized search query 3",
        "optimized search query 4",
        "optimized search query 5"
    ],
    "requires_weather_data": true,
    "geographic_scope": "city|region|province|country"
}

IMPORTANT RULES:
- YOU ARE IN THE YEAR 2026. ONLY SEARCH 2026 INFORMATION.
- Generate 3-5 highly targeted search queries optimized for finding network outage information
- If weather-related, include weather search queries
- Be very specific with location names** (city, neighborhood, province) whenever mentioned.
- Include temporal terms in searches (today, yesterday, January 2026, etc.)
- Focus on sources like news reports, government bulletins, press releases, research papers — no outage maps or carrier pages.
- Return ONLY the JSON, no markdown formatting, no explanations"""

        # Construct user prompt
        user_prompt = f"""Analyze this network outage query:

"{question}"

Extract structured information and generate optimized search queries. Return JSON only."""

        # Call Gemma model
        response = await AIModelClient.call_gemma(
            prompt=user_prompt,
            system_prompt=system_prompt
        )
        
        # Parse JSON response
        try:
            metadata = EventIntelligenceAgent._parse_response(response)
            logger.info(f"✅ Extracted {len(metadata.events)} event(s)")
            logger.info(f"🔍 Generated {len(metadata.search_queries)} search queries")
            return metadata
            
        except Exception as e:
            logger.error(f"💥 Error parsing response: {str(e)}")
            logger.warning("⚠️  Using fallback metadata generation")
            return EventIntelligenceAgent._generate_fallback_metadata(question)
    
    @staticmethod
    def _parse_response(response: str) -> EventMetadata:
        """
        Parse AI model response into EventMetadata
        
        Args:
            response: Raw text response from model
        
        Returns:
            EventMetadata object
        """
        
        # Extract JSON from response (handle markdown code blocks)
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        
        if not json_match:
            raise ValueError("No JSON found in response")
        
        # Parse JSON
        data = json.loads(json_match.group())
        
        # Validate required fields
        if "events" not in data or "search_queries" not in data:
            raise ValueError("Missing required fields in JSON")
        
        # Create EventMetadata object
        metadata = EventMetadata(
            events=data.get("events", []),
            search_queries=data.get("search_queries", [])[:Config.MAX_SEARCH_QUERIES],
            requires_weather_data=data.get("requires_weather_data", False),
            geographic_scope=data.get("geographic_scope", "region")
        )
        
        return metadata
    
    @staticmethod
    def _generate_fallback_metadata(question: str) -> EventMetadata:
        """
        Generate fallback metadata when parsing fails
        
        Args:
            question: Original user question
        
        Returns:
            Basic EventMetadata object
        """
        
        logger.info("🔧 Generating fallback metadata...")
        
        # Extract basic information from question
        question_lower = question.lower()
        
        # Detect event type
        event_type = "unknown"
        if any(word in question_lower for word in ["storm", "ice", "snow", "rain", "weather"]):
            event_type = "weather_related_outage"
        elif any(word in question_lower for word in ["power", "electricity", "grid"]):
            event_type = "power_outage"
        elif any(word in question_lower for word in ["equipment", "tower", "failure"]):
            event_type = "equipment_failure"
        
        # Detect location
        location = "Toronto"  # Default location
        if "toronto" in question_lower:
            location = "Toronto"
        elif "mississauga" in question_lower:
            location = "Mississauga"
        elif "vancouver" in question_lower:
            location = "Vancouver"
        elif "montreal" in question_lower:
            location = "Montreal"
        
        # Detect timeframe
        timeframe = "recent"
        if any(word in question_lower for word in ["today", "now", "current"]):
            timeframe = "today"
        elif any(word in question_lower for word in ["yesterday"]):
            timeframe = "yesterday"
        elif any(word in question_lower for word in ["last week", "this week"]):
            timeframe = "this week"
        
        # Generate basic search queries
        search_queries = [
            f"{location} network outage {timeframe}",
            f"telus {location} service disruption",
            f"{location} cellular network down",
            f"{event_type} {location} telecommunications",
            f"{location} cell tower outage {timeframe}"
        ]
        
        # Check if weather data needed
        requires_weather = event_type == "weather_related_outage"
        
        return EventMetadata(
            events=[{
                "event_type": event_type,
                "primary_location": location,
                "timeframe": timeframe,
                "keywords": question.split()[:5]
            }],
            search_queries=search_queries[:Config.MAX_SEARCH_QUERIES],
            requires_weather_data=requires_weather,
            geographic_scope="city"
        )
    
    @staticmethod
    def validate_metadata(metadata: EventMetadata) -> bool:
        """
        Validate EventMetadata for completeness
        
        Args:
            metadata: EventMetadata to validate
        
        Returns:
            True if valid, False otherwise
        """
        
        if not metadata.events:
            logger.warning("⚠️  No events found in metadata")
            return False
        
        if not metadata.search_queries:
            logger.warning("⚠️  No search queries generated")
            return False
        
        if len(metadata.search_queries) < 3:
            logger.warning(f"⚠️  Only {len(metadata.search_queries)} search queries (recommended: 3-5)")
        
        return True