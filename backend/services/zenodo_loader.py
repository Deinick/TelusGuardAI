import os
from typing import List, Tuple, Dict, Optional

def load_zenodo_series(path: str) -> Tuple[List[int], List[float]]:
    """
    Loads Zenodo r*.txt / s*.txt format:
    time_in_seconds value

    Example:
    0 504.35
    300 482.26
    """
    times: List[int] = []
    values: List[float] = []

    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            t_str, v_str = line.split()
            times.append(int(t_str))
            values.append(float(v_str))

    return times, values


def load_real_incidents(path: str) -> List[Tuple[str, int, int]]:
    """
    Loads data_real_incidents.txt:
    series_id sample_start sample_end

    end=-1 means "to end of series". Returns List[(series_id, start, end)].
    """
    out: List[Tuple[str, int, int]] = []
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) < 3:
                continue
            sid, start, end = parts[0], int(parts[1]), int(parts[2])
            out.append((sid, start, end))
    return out


def load_series_info(path: str) -> Dict[str, str]:
    """
    Loads data_real_info.txt or data_series_info.txt:
    series_id kpi_type

    Returns Dict[series_id, kpi_type] e.g. {"r1": "internet", "r13": "downstream"}.
    """
    out: Dict[str, str] = {}
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(None, 1)
            if len(parts) < 2:
                continue
            out[parts[0]] = parts[1].strip().lower()
    return out


def get_first_series_path_of_type(
    series_info: Dict[str, str],
    base_dir: str,
    series_subdir: str,
    kpi_type: str,
) -> Optional[str]:
    """
    Finds the first series_id in series_info with the given kpi_type and
    returns the path: base_dir / series_subdir / {series_id}.txt
    """
    kpi = kpi_type.lower()
    for sid, k in series_info.items():
        if k == kpi:
            p = os.path.join(base_dir, series_subdir, f"{sid}.txt")
            if os.path.isfile(p):
                return p
    return None


def is_in_anomaly_window(
    series_id: str,
    sample_index: int,
    incidents: List[Tuple[str, int, int]],
) -> bool:
    """
    Returns True if sample_index falls inside any anomaly window for series_id.
    incidents: List[(sid, start, end)]; end=-1 means from start to end of series.
    """
    for sid, start, end in incidents:
        if sid != series_id:
            continue
        if end < 0:
            if sample_index >= start:
                return True
        else:
            if start <= sample_index <= end:
                return True
    return False


def create_baseline_stream(
    zenodo_base_dir: str,
    mode: str,
) -> Tuple[List[float], str, List[Tuple[str, int, int]]]:
    """
    Returns (values, series_id, incidents) for single-baseline mode.

    mode:
      - "real":    data_real, first "internet" (r1), with data_real_incidents.
      - "healthy": data_series, first "internet" (e.g. s1), no incidents.

    incidents: for "healthy" always []. For "real", full incidents list
    (is_in_anomaly_window filters by series_id).
    """
    incidents: List[Tuple[str, int, int]] = []
    info_path_r = os.path.join(zenodo_base_dir, "data_real_info.txt")
    info_path_s = os.path.join(zenodo_base_dir, "data_series_info.txt")
    inc_path = os.path.join(zenodo_base_dir, "data_real_incidents.txt")

    if mode == "real":
        info = load_series_info(info_path_r)
        path = get_first_series_path_of_type(info, zenodo_base_dir, "data_real", "internet")
        if not path:
            raise FileNotFoundError(f"No internet series in data_real under {zenodo_base_dir}")
        if os.path.isfile(inc_path):
            incidents = load_real_incidents(inc_path)
        _, values = load_zenodo_series(path)
        sid = os.path.splitext(os.path.basename(path))[0]
        return (values, sid, incidents)

    if mode == "healthy":
        info = load_series_info(info_path_s)
        path = get_first_series_path_of_type(info, zenodo_base_dir, "data_series", "internet")
        if not path:
            raise FileNotFoundError(f"No internet series in data_series under {zenodo_base_dir}")
        _, values = load_zenodo_series(path)
        sid = os.path.splitext(os.path.basename(path))[0]
        return (values, sid, [])

    raise ValueError(f"create_baseline_stream: mode must be 'real' or 'healthy', got {mode!r}")


def load_multi_baseline(zenodo_base_dir: str) -> Tuple[List[float], List[float], List[Tuple[str, int, int]]]:
    """
    For multi-KPI (internet + downstream): loads r1 (internet) and r13 (downstream)
    from data_real. Returns (internet_values, downstream_values, incidents).
    incidents are from data_real_incidents (used for r1 anomaly windows).
    """
    info = load_series_info(os.path.join(zenodo_base_dir, "data_real_info.txt"))
    path_i = get_first_series_path_of_type(info, zenodo_base_dir, "data_real", "internet")
    path_d = get_first_series_path_of_type(info, zenodo_base_dir, "data_real", "downstream")
    if not path_i:
        raise FileNotFoundError(f"No internet series in data_real under {zenodo_base_dir}")
    if not path_d:
        raise FileNotFoundError(f"No downstream series in data_real under {zenodo_base_dir}")
    _, iv = load_zenodo_series(path_i)
    _, dv = load_zenodo_series(path_d)
    inc_path = os.path.join(zenodo_base_dir, "data_real_incidents.txt")
    incidents = load_real_incidents(inc_path) if os.path.isfile(inc_path) else []
    return (iv, dv, incidents)
