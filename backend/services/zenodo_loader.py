from typing import List, Tuple

def load_zenodo_series(path: str) -> Tuple[List[int], List[float]]:
    """

    Loads Zenodo r1.txt format:
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
