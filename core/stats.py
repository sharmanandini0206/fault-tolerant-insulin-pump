import math
from fault_tolerant_pump.config import STATS_WINDOW_SIZE, MIN_SAFE_GLUCOSE

class RollingStatsTracker:
    """
    An O(1) statistical monitor that detects sensor anomalies
    algebraically using a fixed-capacity circular ring buffer.
    """
    def __init__(self, window_size: int = STATS_WINDOW_SIZE):
        self.window_size = window_size
        self.buffer = [0.0] * window_size
        self.head = 0 
        
        # Accumulators
        self.n = 0
        self.sum_x = 0.0
        self.sum_x_sq = 0.0

    def update(self, val: float) -> None:
        """
        Updates the circular buffer and sliding accumulators with a new reading.
        Time Complexity: O(1)
        """
        if self.n < self.window_size:
            # Buffer is filling up for the first time
            self.buffer[self.n] = val
            self.sum_x += val
            self.sum_x_sq += val ** 2
            self.n += 1
        else:
            # Buffer is full; evict oldest element at head pointer index
            old_val = self.buffer[self.head]
            
            # Subtract old metrics, add new metrics
            self.sum_x = self.sum_x - old_val + val
            self.sum_x_sq = self.sum_x_sq - (old_val ** 2) + (val ** 2)
            
            # Overwrite oldest slot and advance ring pointer
            self.buffer[self.head] = val
            self.head = (self.head + 1) % self.window_size

    @property
    def mean(self) -> float:
        """Returns sliding window mathematical average."""
        if self.n == 0:
            return 0.0
        return self.sum_x / self.n

    @property
    def variance(self) -> float:
        """Returns sliding window variance using the O(1) algebraic formula."""
        if self.n < 2:
            return 0.0
        
        # Calculate variance via identity formula
        var_val = (self.sum_x_sq / self.n) - (self.mean ** 2)
        
        # Shield against fractional floating point rounding noise causing negative variance
        return max(0.0, var_val)

    @property
    def std_dev(self) -> float:
        """Returns sliding window standard deviation."""
        return math.sqrt(self.variance)

    def analyze_anomaly(self, current_val: float) -> str:
        """
        Evaluates the current frame reading against historical variance windows 
        to capture hardware-level degradation before it reaches the control loop.
        """
        # 1. SIGNAL_DROPPED: Immediate plunge below safety parameters
        if current_val < MIN_SAFE_GLUCOSE:
            return "SIGNAL_DROPPED"

        # 2. TELEMETRY_FROZEN: Variance hits zero across a filled window
        # Indicates frozen ADC converter chip, locked register bus, or flatline error
        if self.n == self.window_size and self.variance == 0.0:
            return "TELEMETRY_FROZEN"

        # 3. CRITICAL_NOISE: Standard deviation exceeds standard physiological limits
        # Indicates high-frequency electromagnetic interference from pump motor actuation
        if self.n == self.window_size and self.std_dev > 25.0:
            return "CRITICAL_NOISE"

        return "NOMINAL"