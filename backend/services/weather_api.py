"""
Weather API service for fetching weather conditions
"""

import aiohttp
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
from config import Config
from utils.logger import logger
from utils.cache import cache


class WeatherAPI:
    """
    Fetches weather data from OpenWeatherMap API
    
    Get free API key at: https://openweathermap.org/api
    Free tier: 1,000 calls/day, 60 calls/minute
    """
    
    @staticmethod
    async def get_current_weather(lat: float, lon: float) -> Dict[str, Any]:
        """
        Get current weather conditions for a location
        
        Args:
            lat: Latitude
            lon: Longitude
        
        Returns:
            Dictionary with weather data
        """
        
        # Check cache first
        cache_key = f"weather_current_{lat}_{lon}"
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        logger.info(f"🌤️  Fetching current weather for ({lat:.2f}, {lon:.2f})")
        
        # Check if API key is configured
        if not Config.OPENWEATHER_API_KEY or Config.OPENWEATHER_API_KEY == "your_api_key_here":
            logger.warning("⚠️  Using mock weather data (no API key configured)")
            weather_data = WeatherAPI._generate_mock_weather(lat, lon)
        else:
            logger.info(f"🌐 Using real OpenWeatherMap API with key: {Config.OPENWEATHER_API_KEY[:10]}...")
            weather_data = await WeatherAPI._fetch_real_weather(lat, lon)
        
        # Cache the result
        cache.set(cache_key, weather_data)
        
        return weather_data
    
    @staticmethod
    async def _fetch_real_weather(lat: float, lon: float) -> Dict[str, Any]:
        """
        Fetch real weather data from OpenWeatherMap
        """
        
        url = f"{Config.OPENWEATHER_BASE_URL}/weather"
        params = {
            "lat": lat,
            "lon": lon,
            "appid": Config.OPENWEATHER_API_KEY,
            "units": "metric"  # Celsius
        }
        
        logger.info(f"🌐 Requesting: {url}?lat={lat}&lon={lon}&appid=***&units=metric")
        
        try:
            # Disable SSL verification for API calls
            connector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    
                    logger.info(f"🌐 Weather API Response Status: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        # Parse weather data
                        return {
                            "condition": data["weather"][0]["main"].lower(),
                            "description": data["weather"][0]["description"],
                            "temperature": data["main"]["temp"],
                            "feels_like": data["main"]["feels_like"],
                            "humidity": data["main"]["humidity"],
                            "wind_speed": data["wind"]["speed"] * 3.6,  # Convert m/s to km/h
                            "precipitation": data.get("rain", {}).get("1h", 0),
                            "visibility": data.get("visibility", 10000) / 1000,  # Convert to km
                            "warnings": WeatherAPI._determine_warnings(data),
                            "severity": WeatherAPI._determine_severity(data)
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Weather API error: {response.status}")
                        logger.error(f"❌ Response body: {error_text[:200]}")
                        logger.error(f"❌ Request URL: {url}")
                        logger.error(f"❌ Request params: lat={lat}, lon={lon}, appid={'*' * 10}, units=metric")
                        return WeatherAPI._generate_mock_weather(lat, lon)
                        
        except asyncio.TimeoutError:
            logger.error("⏰ Weather API timeout")
            return WeatherAPI._generate_mock_weather(lat, lon)
        except Exception as e:
            logger.error(f"💥 Weather API error: {str(e)}")
            return WeatherAPI._generate_mock_weather(lat, lon)
    
    @staticmethod
    def _determine_warnings(data: Dict[str, Any]) -> list:
        """Determine weather warnings based on conditions"""
        warnings = []
        
        # Temperature warnings
        temp = data["main"]["temp"]
        if temp < -20:
            warnings.append("Extreme cold warning")
        elif temp < -10:
            warnings.append("Cold weather advisory")
        
        # Wind warnings
        wind_speed = data["wind"]["speed"] * 3.6  # m/s to km/h
        if wind_speed > 70:
            warnings.append("High wind warning")
        elif wind_speed > 50:
            warnings.append("Wind advisory")
        
        # Precipitation warnings
        if "rain" in data and data["rain"].get("1h", 0) > 10:
            warnings.append("Heavy rain warning")
        if "snow" in data and data["snow"].get("1h", 0) > 5:
            warnings.append("Heavy snow warning")
        
        # Visibility warnings
        visibility = data.get("visibility", 10000)
        if visibility < 1000:
            warnings.append("Poor visibility warning")
        
        return warnings
    
    @staticmethod
    def _determine_severity(data: Dict[str, Any]) -> str:
        """Determine overall weather severity"""
        
        # Check for severe conditions
        temp = data["main"]["temp"]
        wind_speed = data["wind"]["speed"] * 3.6
        rain = data.get("rain", {}).get("1h", 0)
        snow = data.get("snow", {}).get("1h", 0)
        
        if temp < -20 or wind_speed > 70 or rain > 15 or snow > 10:
            return "severe"
        elif temp < -10 or wind_speed > 50 or rain > 10 or snow > 5:
            return "moderate"
        else:
            return "mild"
    
    @staticmethod
    def _generate_mock_weather(lat: float, lon: float) -> Dict[str, Any]:
        """
        Generate mock weather data for testing
        """
        return {
            "condition": "ice_storm",
            "description": "freezing rain and ice accumulation",
            "temperature": -5,
            "feels_like": -12,
            "humidity": 95,
            "wind_speed": 45,
            "precipitation": "15mm ice accumulation",
            "visibility": 2.5,
            "warnings": [
                "Ice storm warning",
                "Power outage risk",
                "Travel not recommended"
            ],
            "severity": "severe",
            "_note": "This is mock data for testing"
        }
    
    @staticmethod
    async def get_historical_weather(
        lat: float,
        lon: float,
        date: datetime
    ) -> Dict[str, Any]:
        """
        Get historical weather data for a specific date
        
        Note: Requires paid OpenWeatherMap subscription
        """
        logger.info(f"📅 Fetching historical weather for {date.strftime('%Y-%m-%d')}")
        
        # Mock implementation - would need paid API access
        return WeatherAPI._generate_mock_weather(lat, lon)
    
    @staticmethod
    async def get_weather_multiple_locations(
        locations: list[tuple[float, float]]
    ) -> Dict[tuple[float, float], Dict[str, Any]]:
        """
        Fetch weather for multiple locations in parallel
        
        Args:
            locations: List of (lat, lon) tuples
        
        Returns:
            Dictionary mapping locations to weather data
        """
        logger.info(f"🌦️  Fetching weather for {len(locations)} locations")
        
        tasks = [
            WeatherAPI.get_current_weather(lat, lon)
            for lat, lon in locations
        ]
        
        results = await asyncio.gather(*tasks)
        
        return {
            location: weather
            for location, weather in zip(locations, results)
        }

