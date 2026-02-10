"""
Moving average smoothing for landmark coordinates.
Reduces jitter from raw MediaPipe detections.
"""
from collections import deque


class MovingAverage:
    """Simple moving average over a sliding window of values."""

    def __init__(self, window_size: int = 3):
        self._buffer = deque(maxlen=window_size)

    def update(self, value: float) -> float:
        """Add a value and return the smoothed (averaged) result."""
        self._buffer.append(value)
        return sum(self._buffer) / len(self._buffer)

    def reset(self):
        """Clear the buffer."""
        self._buffer.clear()
