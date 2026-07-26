"""
Configuration settings for Network Impact Analyzer
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Central configuration for all AI models and APIs"""
    
    # ========================================================================
    # AI MODEL ENDPOINTS
    # ========================================================================
    
    GEMMA_ENDPOINT = os.getenv("GEMMA_ENDPOINT", "https://gemma-3-27b-3ca9s.paas.ai.telus.com")
    GEMMA_TOKEN = os.getenv("GEMMA_TOKEN")

    DEEPSEEK_ENDPOINT = os.getenv("DEEPSEEK_ENDPOINT", "https://deepseekv32-3ca9s.paas.ai.telus.com")
    DEEPSEEK_TOKEN = os.getenv("DEEPSEEK_TOKEN")

    GPT_ENDPOINT = os.getenv("GPT_ENDPOINT", "https://rr-test-gpt-120-9219s.paas.ai.telus.com")
    GPT_TOKEN = os.getenv("GPT_TOKEN")

    QWEN_CODER_ENDPOINT = os.getenv("QWEN_CODER_ENDPOINT", "https://qwen3coder30b-3ca9s.paas.ai.telus.com")
    QWEN_CODER_TOKEN = os.getenv("QWEN_CODER_TOKEN")

    QWEN_EMB_ENDPOINT = os.getenv("QWEN_EMB_ENDPOINT", "https://qwen-emb-3ca9s.paas.ai.telus.com")
    QWEN_EMB_TOKEN = os.getenv("QWEN_EMB_TOKEN")

    # ========================================================================
    # EXTERNAL APIS
    # ========================================================================

    OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
    OPENWEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5"
    
    # ========================================================================
    # SYSTEM SETTINGS
    # ========================================================================
    
    # API limits
    MAX_SEARCH_QUERIES = 5
    REQUEST_TIMEOUT = 30  # seconds
    
    # Caching
    CACHE_TTL = 300  # 5 minutes in seconds
    
    # Analysis limits
    MAX_AREAS_RETURNED = 10
    MIN_CONFIDENCE_THRESHOLD = 0.65
    
    # Flask settings
    FLASK_HOST = "0.0.0.0"
    FLASK_PORT = 5001
    FLASK_DEBUG = True
    
    # ========================================================================
    # MODEL PARAMETERS
    # ========================================================================
    
    # Default temperature settings for different agents
    TEMPERATURE_EVENT_INTELLIGENCE = 0.3  # Lower = more focused
    TEMPERATURE_WEB_INTELLIGENCE = 0.5
    TEMPERATURE_GEOSPATIAL_REASONING = 0.4
    
    # Token limits
    MAX_TOKENS_EVENT_INTELLIGENCE = 1000
    MAX_TOKENS_WEB_INTELLIGENCE = 1500
    MAX_TOKENS_GEOSPATIAL_REASONING = 3000