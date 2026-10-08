"""fines.py - Overdue duration and fine calculation rules.

Rules (all amounts in Rs):
  * Grace period : 1 day after the due date is free.
  * Days 1-7   after grace : Rs 5  per day
  * Days 8-14  after grace : Rs 10 per day
  * Days 15+   after grace : Rs 20 per day
  * Maximum fine per loan  : Rs 500
"""
from datetime import date
from typing import Optional

import numpy as np

GRACE_DAYS = 1
TIER1_DAYS, TIER1_RATE = 7, 5.0
TIER2_DAYS, TIER2_RATE = 7, 10.0   # next 7 days (days 8-14)
TIER3_RATE = 20.0
MAX_FINE = 500.0


def overdue_days(due: date, returned: Optional[date] = None,
                 today: Optional[date] = None) -> int:
    """Number of days late (0 if on time). Uses today's date if not returned."""
    end = returned or today or date.today()
    return max((end - due).days, 0)


def calculate_fines_array(days_late) -> np.ndarray:
    """Vectorised fine calculation for an array of days-late values."""
    days = np.asarray(days_late, dtype=float)
    if np.any(days < 0):
        raise ValueError("days_late cannot be negative")
    chargeable = np.maximum(days - GRACE_DAYS, 0)
    part1 = np.minimum(chargeable, TIER1_DAYS) * TIER1_RATE
    part2 = np.clip(chargeable - TIER1_DAYS, 0, TIER2_DAYS) * TIER2_RATE
    part3 = np.maximum(chargeable - TIER1_DAYS - TIER2_DAYS, 0) * TIER3_RATE
    return np.minimum(part1 + part2 + part3, MAX_FINE)


def calculate_fine(days_late: int) -> float:
    """Fine for a single loan."""
    if not isinstance(days_late, (int, np.integer)) or days_late < 0:
        raise ValueError("days_late must be a non-negative integer")
    return float(calculate_fines_array([days_late])[0])
