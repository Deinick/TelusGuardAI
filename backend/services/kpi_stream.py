import time
from typing import List, Tuple


class ZenodoStream:
    """
    Plays through a single Zenodo value series in a loop.
    next_value() returns the current value and advances; last_index is the
    sample index of the value that was just returned (for anomaly-window checks).
    """

    def __init__(self, values: List[float]):
        self.values = values
        self.idx = 0
        self.last_index: int = 0

    def next_value(self) -> float:
        val = self.values[self.idx]
        self.last_index = self.idx
        self.idx = (self.idx + 1) % len(self.values)
        return val

    def run_live(self, tick_seconds: float = 1.0) -> None:
        while True:
            baseline = self.next_value()
            print({"baseline_internet": baseline})
            time.sleep(tick_seconds)


class DualZenodoStream:
    """
    Two ZenodoStreams in sync; next_value() returns (internet, downstream).
    last_index matches the internet stream (for r1 anomaly-window checks).
    """

    def __init__(self, internet_values: List[float], downstream_values: List[float]):
        self._internet = ZenodoStream(internet_values)
        self._downstream = ZenodoStream(downstream_values)

    @property
    def last_index(self) -> int:
        return self._internet.last_index

    def next_value(self) -> Tuple[float, float]:
        return self._internet.next_value(), self._downstream.next_value()
