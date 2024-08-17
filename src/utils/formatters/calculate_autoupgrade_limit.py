def calculate_autoupgrade_limit(earn_passive_per_hour: int, max_taps: int) -> int:
    return (earn_passive_per_hour * 24) + (max_taps * 24) // 2
