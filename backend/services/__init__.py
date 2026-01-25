# services: AI (ai_client, weather_api, web_search) + Zenodo/NetOps
# zenodo_loader: load_zenodo_series, load_real_incidents, load_series_info,
#   get_first_series_path_of_type, is_in_anomaly_window,
#   create_baseline_stream(mode='real'|'healthy'), load_multi_baseline
# kpi_stream: ZenodoStream (last_index), DualZenodoStream
# tower_loader: load_towers_json, filter_towers_bbox(limit=None), CANADA_BBOX
# tower_kpi_generator: in_real_anomaly, baseline_downstream
# Import from submodules, e.g.:
#   from services.zenodo_loader import create_baseline_stream, is_in_anomaly_window
#   from services.kpi_stream import ZenodoStream, DualZenodoStream
