"""
Tracks metrics across completed reps for trend analysis and fatigue detection.
"""


class RepHistoryTracker:
    """
    Stores per-rep metrics in a sliding window buffer.

    Usage:
        history = RepHistoryTracker()
        history.record({'hip_drop': 0.12, 'worst_back_angle': 160})
        trend = history.get_trend('hip_drop')
    """

    MAX_HISTORY = 50

    def __init__(self):
        self.rep_history = []

    def record(self, metrics: dict):
        """Record metrics from a completed rep."""
        self.rep_history.append(metrics)
        if len(self.rep_history) > self.MAX_HISTORY:
            self.rep_history.pop(0)

    def get_average(self, key: str, last_n: int = None) -> float | None:
        """
        Average of a metric over last N reps (or all if last_n is None).

        Returns None if no data for the key.
        """
        reps = self.rep_history[-last_n:] if last_n else self.rep_history
        values = [r[key] for r in reps if key in r and r[key] is not None]
        if not values:
            return None
        return sum(values) / len(values)

    def get_trend(self, key: str, last_n: int = 5) -> dict:
        """
        Returns stats for a metric over the last N reps.

        Returns:
            dict with 'avg', 'min', 'max', 'count' keys.
            All values are None if no data.
        """
        reps = self.rep_history[-last_n:] if last_n else self.rep_history
        values = [r[key] for r in reps if key in r and r[key] is not None]

        if not values:
            return {'avg': None, 'min': None, 'max': None, 'count': 0}

        return {
            'avg': sum(values) / len(values),
            'min': min(values),
            'max': max(values),
            'count': len(values),
        }

    def is_degrading(self, key: str, threshold: float, last_n: int = 3) -> bool:
        """
        True if the average of the last N reps is below the threshold.

        Returns False if insufficient data.
        """
        avg = self.get_average(key, last_n)
        if avg is None:
            return False
        return avg < threshold

    def reset(self):
        """Clear all history."""
        self.rep_history.clear()
