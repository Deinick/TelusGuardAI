"""
Flask application for Network Impact Analyzer
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import asyncio
from datetime import datetime
from orchestrator import NetworkImpactOrchestrator
from utils.logger import logger
from utils.cache import cache
from config import Config
from services.kpi_service import get_kpi_service


# ============================================================================
# FLASK APP SETUP
# ============================================================================

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend integration

# Configure Flask
app.config['JSON_SORT_KEYS'] = False
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def run_async(coro):
    """
    Helper to run async functions in Flask sync context
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ============================================================================
# API ROUTES
# ============================================================================

@app.route('/', methods=['GET'])
def home():
    """
    Home endpoint with API information
    """
    return jsonify({
        "service": "Network Impact Analyzer",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "health": "/health",
            "analyze": "/api/analyze-network-impact (POST)",
            "kpis": "/api/kpis (POST)",
            "cache_stats": "/api/cache-stats (GET)",
            "cached_queries": "/api/cached-queries (GET)",
            "clear_cache": "/api/clear-cache (POST)"
        },
        "documentation": "/api/docs"
    }), 200


@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint
    """
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "config": {
            "max_search_queries": Config.MAX_SEARCH_QUERIES,
            "cache_ttl": Config.CACHE_TTL,
            "max_areas_returned": Config.MAX_AREAS_RETURNED
        }
    }), 200


@app.route('/api/analyze-network-impact', methods=['POST'])
def analyze_network_impact():
    """
    Main API endpoint for network impact analysis
    
    Request body:
    {
        "question": "What areas were affected by the ice storm?",
        "options": {
            "max_areas": 10,
            "min_confidence": 0.7,
            "include_reasoning": true
        }
    }
    
    Response:
    {
        "query": "...",
        "timestamp": "...",
        "summary": "...",
        "events": [...],
        "total_events": 2,
        "total_affected_areas": 5,
        "analysis_metadata": {...}
    }
    """
    try:
        # Parse request
        data = request.get_json()
        
        if not data:
            return jsonify({
                "error": "Invalid request",
                "message": "Request body must be JSON"
            }), 400
        
        if 'question' not in data:
            return jsonify({
                "error": "Missing required field",
                "message": "Field 'question' is required"
            }), 400
        
        question = data['question']
        options = data.get('options', {})
        
        # Validate question
        is_valid, error_msg = NetworkImpactOrchestrator.validate_question(question)
        if not is_valid:
            return jsonify({
                "error": "Invalid question",
                "message": error_msg
            }), 400
        
        logger.info(f"📨 Received analysis request: '{question[:50]}...'")
        
        # Run orchestrator
        result = run_async(
            NetworkImpactOrchestrator.analyze(question, options)
        )
        
        # Convert to dict for JSON response
        response_data = result.to_dict()
        
        logger.info(f"✅ Analysis complete, returning {len(result.events)} events")
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"💥 Error in analyze endpoint: {str(e)}")
        return jsonify({
            "error": "Internal server error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500


@app.route('/api/kpis', methods=['POST'])
def get_kpis():
    """
    Get KPIs for specified tower IDs
    
    Request body:
    {
        "tower_ids": ["tower_1", "tower_2", ...],
        "options": {
            "mode": "sim",
            "tick_ms": 1000
        }
    }
    
    Response:
    {
        "timestamp": "ISO 8601 timestamp",
        "kpis": {
            "tower_1": {
                "traffic": 0.65,
                "latency_ms": 45,
                "packet_loss": 0.02,
                "energy": 0.7,
                "status": "ok"
            },
            ...
        }
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "error": "Invalid request",
                "message": "Request body must be JSON"
            }), 400
        
        tower_ids = data.get('tower_ids', [])
        
        if not tower_ids or not isinstance(tower_ids, list):
            return jsonify({
                "error": "Missing or invalid field",
                "message": "Field 'tower_ids' is required and must be a non-empty list"
            }), 400
        
        # Get KPI service and fetch KPIs
        kpi_service = get_kpi_service()
        kpis = kpi_service.get_kpis(tower_ids)
        
        logger.info(f"📊 Returning KPIs for {len(kpis)} towers")
        
        return jsonify({
            "timestamp": datetime.now().isoformat(),
            "kpis": kpis
        }), 200
        
    except Exception as e:
        logger.error(f"💥 Error in KPIs endpoint: {str(e)}")
        return jsonify({
            "error": "Internal server error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500


@app.route('/api/cache-stats', methods=['GET'])
def get_cache_stats():
    """
    Get cache statistics
    """
    stats = cache.get_stats()
    return jsonify({
        "cache_stats": stats,
        "timestamp": datetime.now().isoformat()
    }), 200


@app.route('/api/cached-queries', methods=['GET'])
def get_cached_queries():
    """
    Get list of cached queries
    """
    cached_keys = [k for k in cache.cache.keys() if k.startswith("analysis_")]
    queries = [k.replace("analysis_", "") for k in cached_keys]
    
    return jsonify({
        "cached_queries": queries,
        "count": len(queries),
        "timestamp": datetime.now().isoformat()
    }), 200


@app.route('/api/clear-cache', methods=['POST'])
def clear_cache():
    """
    Clear all cached results
    """
    cache.clear()
    logger.info("🗑️  Cache cleared via API")
    
    return jsonify({
        "message": "Cache cleared successfully",
        "timestamp": datetime.now().isoformat()
    }), 200


@app.route('/api/docs', methods=['GET'])
def api_documentation():
    """
    API documentation endpoint
    """
    docs = {
        "api_name": "Network Impact Analyzer API",
        "version": "1.0.0",
        "description": "Analyzes network service disruptions during events using multi-agent AI system",
        
        "endpoints": {
            "POST /api/analyze-network-impact": {
                "description": "Analyze network impact from natural language query",
                "request_body": {
                    "question": "string (required) - Natural language question about network outages",
                    "options": {
                        "max_areas": "integer (optional, default: 10) - Maximum areas to return",
                        "min_confidence": "float (optional, default: 0.65) - Minimum confidence threshold",
                        "include_reasoning": "boolean (optional, default: true) - Include detailed reasoning"
                    }
                },
                "response": {
                    "query": "Original question",
                    "timestamp": "ISO 8601 timestamp",
                    "summary": "Human-readable summary",
                    "events": "Array of event objects",
                    "total_events": "Number of events",
                    "total_affected_areas": "Number of affected areas",
                    "analysis_metadata": "Analysis metadata"
                },
                "example_request": {
                    "question": "What areas were affected by the ice storm in Toronto?",
                    "options": {
                        "max_areas": 10,
                        "min_confidence": 0.7
                    }
                }
            },
            
            "GET /health": {
                "description": "Health check endpoint",
                "response": {
                    "status": "healthy|degraded|down",
                    "timestamp": "ISO 8601 timestamp"
                }
            },
            
            "GET /api/cache-stats": {
                "description": "Get cache statistics",
                "response": {
                    "cache_stats": {
                        "total_items": "Number",
                        "active_items": "Number",
                        "expired_items": "Number"
                    }
                }
            },
            
            "POST /api/clear-cache": {
                "description": "Clear all cached analysis results",
                "response": {
                    "message": "Success message"
                }
            }
        },
        
        "data_models": {
            "Event": {
                "event_id": "string - Unique identifier",
                "event_name": "string - Descriptive name",
                "event_type": "string - Type of event",
                "timeframe": "string - When event occurred",
                "affected_areas": "Array of AffectedArea objects"
            },
            
            "AffectedArea": {
                "area_name": "string - Geographic area name",
                "severity": "string - critical|high|moderate|low",
                "lat_range": "[min_lat, max_lat] - Array of floats",
                "long_range": "[min_long, max_long] - Array of floats",
                "center": "Object {lat, long} - Center coordinates",
                "reasoning": "string - Detailed explanation",
                "estimated_impact": "string - Estimated affected users",
                "confidence": "float - Confidence score (0-1)",
                "data_points": "integer - Supporting data points"
            }
        },
        
        "notes": {
            "caching": "Results are cached for 5 minutes to improve performance",
            "rate_limiting": "Currently no rate limiting implemented",
            "authentication": "Currently no authentication required"
        }
    }
    
    return jsonify(docs), 200


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        "error": "Not found",
        "message": "The requested endpoint does not exist",
        "available_endpoints": [
            "/",
            "/health",
            "/api/analyze-network-impact",
            "/api/kpis",
            "/api/cache-stats",
            "/api/cached-queries",
            "/api/clear-cache",
            "/api/docs"
        ]
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({
        "error": "Internal server error",
        "message": "An unexpected error occurred",
        "timestamp": datetime.now().isoformat()
    }), 500


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == '__main__':
    logger.info("=" * 80)
    logger.info("🌐 NETWORK IMPACT ANALYZER STARTING")
    logger.info("=" * 80)
    logger.info(f"🔧 Configuration:")
    logger.info(f"   - Max search queries: {Config.MAX_SEARCH_QUERIES}")
    logger.info(f"   - Cache TTL: {Config.CACHE_TTL}s")
    logger.info(f"   - Max areas: {Config.MAX_AREAS_RETURNED}")
    logger.info(f"   - Min confidence: {Config.MIN_CONFIDENCE_THRESHOLD}")
    logger.info("=" * 80)
    logger.info(f"📡 AI Model Endpoints:")
    logger.info(f"   - Gemma: {Config.GEMMA_ENDPOINT}")
    logger.info(f"   - DeepSeek: {Config.DEEPSEEK_ENDPOINT}")
    logger.info(f"   - GPT: {Config.GPT_ENDPOINT}")
    logger.info("=" * 80)
    logger.info(f"🚀 Starting Flask server on {Config.FLASK_HOST}:{Config.FLASK_PORT}")
    logger.info("=" * 80)
    
    # Run Flask app
    app.run(
        host=Config.FLASK_HOST,
        port=Config.FLASK_PORT,
        debug=Config.FLASK_DEBUG,
        threaded=True
    )