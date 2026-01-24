import json
from typing import List, Dict, Any, Tuple

def load_towers_json(path: str) -> List[Dict[str, Any]]: 
    with open(path, "r") as f: 
        return json.load(f)
    
def filter_towers_bbox(
        towers: List[Dict[str, Any]], 
        lat_min: float, lat_max: float,
        lon_min: float, lon_max: float,
        limit: int = 80
) -> List[Dict[str, Any]]:
    """
    Filters towers inside a bounding box (good for one city region).
    Limit keeps UI fast.    
    """

    selected = [
        t for t in towers
        if lat_min <= t["lat"] <= lat_max and lon_min <= t["lon"] <= lon_max
    ]
    return selected[:limit]

VANCOUVER_BBOX = (49.20, 49.33, -123.25, -123.00)
