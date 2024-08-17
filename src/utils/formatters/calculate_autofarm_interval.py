import random
from typing import Optional


def calculate_autofarm_interval(
    available_taps: Optional[int] = None,
    max_taps: Optional[int] = None,
    taps_recover_per_sec: Optional[int] = None,
) -> int:
    """Calculate autofarm interval, return seconds"""
    _, _, _ = available_taps, max_taps, taps_recover_per_sec
    # cr = (max_taps - available_taps) // taps_recover_per_sec
    return random.randint(523, 1291)
