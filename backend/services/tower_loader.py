import json
from typing import List, Dict, Any, Tuple, Optional

def load_towers_json(path: str) -> List[Dict[str, Any]]: 
    with open(path, "r") as f: 
        return json.load(f)
    
def filter_towers_bbox(
        towers: List[Dict[str, Any]], 
        lat_min: float, lat_max: float,
        lon_min: float, lon_max: float,
        limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Filters towers inside a bounding box. Use CANADA_BBOX for nation-wide.

    limit: max towers to return; None = no limit (all in bbox).
    """
    selected = [
        t for t in towers
        if lat_min <= t["lat"] <= lat_max and lon_min <= t["lon"] <= lon_max
    ]
    return selected if limit is None else selected[:limit]


# Canada-wide: ~41°N–84°N, ~142°W–52°W (all provinces/territories)
CANADA_BBOX = (41.0, 84.0, -142.0, -52.0)
