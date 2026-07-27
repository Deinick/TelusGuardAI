import time 
from typing import List

class ZenodoStream: 

    def __init__(self, values: List[float]):
        self.values = values
        self.idx = 0

    def next_value(self) -> float:
        val = self.values[self.idx]
        self.idx = (self.idx + 1) % len(self.values)
        return val 
    
    def run_live(self, tick_seconds: float = 1.0): 
        while True:
            baseline = self.next_value()
            print({"baseline_internet": baseline})
            time.sleep(tick_seconds)
