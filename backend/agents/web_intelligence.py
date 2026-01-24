"""
Agent 2: Web Intelligence Agent
Gathers data from web searches and weather APIs
"""

import asyncio
from typing import Dict, Any, Optional
from models.data_models import EventMetadata, IntelligenceData
from services.web_search import WebSearcher
from services.weather_api import WeatherAPI
from utils.logger import logger, timing_decorator


class WebIntelligenceAgent:
    """
    Aggregates data from multiple sources:
    - Web search results (news, social media, forums)
    - Weather data (when applicable)
    
    Executes searches in parallel for optimal performance
    """
    
    @staticmethod
    @timing_decorator
    async def gather_intelligence(event_metadata: EventMetadata) -> IntelligenceData:
        """
        Gather data from all available sources
        
        Args:
            event_metadata: Structured event information from Event Intelligence Agent
        
        Returns:
            IntelligenceData object with all gathered information
        """
        
        logger.info("🤖 Agent 2: Web Intelligence - Gathering data...")
        
        # Execute web searches and weather fetching in parallel
        web_task = WebIntelligenceAgent._gather_web_data(event_metadata)
        weather_task = WebIntelligenceAgent._gather_weather_data(event_metadata)
        
        # Await both tasks concurrently
        web_results, weather_data = await asyncio.gather(web_task, weather_task)
        
        # Compile intelligence data
        intelligence = IntelligenceData(
            web_results=web_results,
            weather_data=weather_data,
            total_data_points=len(web_results),
            search_queries_used=event_metadata.search_queries
        )
        
        logger.info(f"✅ Intelligence gathering complete")
        logger.info(f"📊 Collected {len(web_results)} web results")
        if weather_data:
            logger.info(f"🌦️  Weather data included")
        
        return intelligence
    
    @staticmethod
    async def _gather_web_data(event_metadata: EventMetadata) -> list:
        """
        Execute web searches for all queries
        
        Args:
            event_metadata: Event metadata with search queries
        
        Returns:
            List of search results
        """
        
        search_queries = event_metadata.search_queries
        logger.info(f"🔍 Executing {len(search_queries)} web searches...")
        
        # Execute all searches in parallel
        results = await WebSearcher.search_multiple(
            queries=search_queries,
            num_results=10
        )
        
        # Deduplicate results based on URL
        unique_results = WebIntelligenceAgent._deduplicate_results(results)
        
        logger.info(f"📄 Collected {len(unique_results)} unique results")
        
        return unique_results
    
    @staticmethod
    async def _gather_weather_data(event_metadata: EventMetadata) -> Optional[Dict[str, Any]]:
        """
        Fetch weather data if required
        
        Args:
            event_metadata: Event metadata
        
        Returns:
            Weather data dictionary or None
        """
        
        if not event_metadata.requires_weather_data:
            logger.info("⏭️  Weather data not required for this query")
            return None
        
        logger.info("🌤️  Fetching weather data...")
        
        # Extract location coordinates from first event
        # TODO: In production, use geocoding service to convert location names to coordinates
        location_coords = WebIntelligenceAgent._get_location_coordinates(event_metadata)
        
        if not location_coords:
            logger.warning("⚠️  Could not determine coordinates, skipping weather data")
            return None
        
        lat, lon = location_coords
        
        try:
            weather_data = await WeatherAPI.get_current_weather(lat, lon)
            logger.info(f"✅ Weather data retrieved: {weather_data.get('condition', 'unknown')}")
            return weather_data
        except Exception as e:
            logger.error(f"❌ Error fetching weather data: {str(e)}")
            return None
    
    @staticmethod
    def _get_location_coordinates(event_metadata: EventMetadata) -> Optional[tuple[float, float]]:
        """
        Convert location name to coordinates
        
        TODO: Integrate with geocoding service (Google Geocoding API, etc.)
        For now, using hardcoded coordinates for common cities
        
        Args:
            event_metadata: Event metadata with location info
        
        Returns:
            (latitude, longitude) tuple or None
        """
        
        if not event_metadata.events:
            return None
        
        location = event_metadata.events[0].get("primary_location", "").lower()
        
        # Hardcoded coordinates for common Canadian cities
        # TODO: Replace with real geocoding service
        CITY_COORDS = {
            "toronto": (43.6532, -79.3832),
            "mississauga": (43.5890, -79.6441),
            "vancouver": (49.2827, -123.1207),
            "montreal": (45.5017, -73.5673),
            "calgary": (51.0447, -114.0719),
            "ottawa": (45.4215, -75.6972),
            "edmonton": (53.5461, -113.4938),
            "winnipeg": (49.8951, -97.1384),
            "quebec city": (46.8139, -71.2080),
            "hamilton": (43.2557, -79.8711),
        }
        
        for city, coords in CITY_COORDS.items():
            if city in location:
                logger.info(f"📍 Using coordinates for {city.title()}: {coords}")
                return coords
        
        # Default to Toronto if location not found
        logger.warning(f"⚠️  Location '{location}' not found, defaulting to Toronto")
        return CITY_COORDS["toronto"]
    
    @staticmethod
    def _deduplicate_results(results: list) -> list:
        """
        Remove duplicate search results based on URL
        
        Args:
            results: List of search result dictionaries
        
        Returns:
            Deduplicated list
        """
        
        seen_urls = set()
        unique_results = []
        
        for result in results:
            url = result.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)
        
        removed_count = len(results) - len(unique_results)
        if removed_count > 0:
            logger.info(f"🧹 Removed {removed_count} duplicate results")
        
        return unique_results
    
    @staticmethod
    def rank_results_by_relevance(results: list, keywords: list) -> list:
        """
        Rank search results by relevance to query keywords
        
        Args:
            results: List of search results
            keywords: List of relevant keywords
        
        Returns:
            Sorted list of results (most relevant first)
        """
        
        def relevance_score(result: dict) -> float:
            """Calculate relevance score for a result"""
            text = f"{result.get('title', '')} {result.get('snippet', '')}".lower()
            
            # Count keyword matches
            matches = sum(1 for keyword in keywords if keyword.lower() in text)
            
            # Bonus for recent results (if date available)
            recency_bonus = 0.0
            # Could add date parsing here
            
            return matches + recency_bonus
        
        # Sort by relevance score (descending)
        sorted_results = sorted(
            results,
            key=relevance_score,
            reverse=True
        )
        
        logger.info("📊 Results ranked by relevance")
        return sorted_results
    
    @staticmethod
    async def enrich_with_additional_sources(
        intelligence_data: IntelligenceData
    ) -> IntelligenceData:
        """
        Optionally enrich data with additional sources
        (e.g., social media APIs, news feeds, etc.)
        
        Args:
            intelligence_data: Existing intelligence data
        
        Returns:
            Enriched intelligence data
        """
        
        # TODO: Add integrations with additional data sources
        # - Twitter API (for real-time outage reports)
        # - Reddit API (for community discussions)
        # - News RSS feeds
        # - Official carrier status pages
        
        logger.info("ℹ️  Additional source enrichment not yet implemented")
        return intelligence_data