import math
from fault_tolerant_pump.config import STATS_WINDOW_SIZE, MIN_SAFE_GLUCOSE

class RollingStatsTracker:
    """
    O(1) statistical anomaly monitor using a fixed-capacity circular ring buffer.
    Tracks mean and variance algebraically without scanning the array.
    """
    def __init__(self, window_size: int = STATS_WINDOW_SIZE):
        self.window_size = window_size
        self.buffer = [0.0] * window_size
        self.head = 0
        self.n = 0
        self.sum_x = 0.0
        self.sum_x_sq = 0.0

    def update(self, val: float) -> None:
        """Inserts a new reading and evicts the oldest. O(1) time complexity."""
        if self.n < self.window_size:
            self.buffer[self.n] = val
            self.sum_x    += val
            self.sum_x_sq += val ** 2
            self.n += 1
        else:
            old_val = self.buffer[self.head]
            self.sum_x    = self.sum_x    - old_val + val
            self.sum_x_sq = self.sum_x_sq - (old_val ** 2) + (val ** 2)
            self.buffer[self.head] = val
            self.head = (self.head + 1) % self.window_size

    @property
    def mean(self) -> float:
        if self.n == 0:
            return 0.0
        return self.sum_x / self.n

    @property
    def variance(self) -> float:
        if self.n < 2:
            return 0.0
        var_val = (self.sum_x_sq / self.n) - (self.mean ** 2)
        return max(0.0, var_val)

    @property
    def std_dev(self) -> float:
        return math.sqrt(self.variance)

    def analyze_anomaly(self, current_val: float) -> str | None:
        """
        Evaluates the current frame against historical variance to detect faults.
        """
        if current_val < MIN_SAFE_GLUCOSE:
            return "SIGNAL_DROPPED"

        if self.n == self.window_size and self.variance == 0.0:
            return "TELEMETRY_FROZEN"

        if self.n == self.window_size and self.std_dev > 25.0:
            return "CRITICAL_NOISE"

        return None 