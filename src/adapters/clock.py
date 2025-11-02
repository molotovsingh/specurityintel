"""
Clock Adapters for UAM Compliance Intelligence System.

Provides system clock and fixed clock implementations for testing.
"""

from datetime import datetime
from ..interfaces.ports import Clock


class SystemClock(Clock):
    """
    System clock adapter that returns actual system time.

    Use in production.

    Example:
        clock = SystemClock()
        timestamp = clock.now()
    """

    def now(self) -> datetime:
        """Get current system time."""
        return datetime.now()


class FixedClock(Clock):
    """
    Fixed clock adapter that returns predetermined time.

    Use in testing for deterministic timestamps.

    Example:
        clock = FixedClock(datetime(2025, 11, 2, 9, 0))
        timestamp = clock.now()  # Always returns 2025-11-02 09:00:00
    """

    def __init__(self, fixed_time: datetime):
        self.fixed_time = fixed_time

    def now(self) -> datetime:
        """Get fixed time."""
        return self.fixed_time
