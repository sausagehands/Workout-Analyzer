class MovementTracker:
    """
    Tracks baseline + peak for a single metric (hip_y, wrist_y, etc)
    """

    def __init__(self, mode="down"):
        """
        mode:
            "down" → peak = max (hip drop, shoulder drop)
            "up"   → peak = min (curl wrist rise)
        """
        self.mode = mode
        self.baseline = None
        self.peak = None

    def reset_peak(self):
        self.peak = None

    def update(self, value):
        if value is None:
            return

        # baseline tracking
        if self.baseline is None:
            self.baseline = value
        else:
            if self.mode == "down":
                self.baseline = min(self.baseline, value)
            else:
                self.baseline = max(self.baseline, value)

        # peak tracking
        if self.peak is None:
            self.peak = value
        else:
            if self.mode == "down":
                self.peak = max(self.peak, value)
            else:
                self.peak = min(self.peak, value)

    def delta(self):
        if self.baseline is None or self.peak is None:
            return 0

        if self.mode == "down":
            return self.peak - self.baseline
        else:
            return self.baseline - self.peak
