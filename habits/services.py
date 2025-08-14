from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from typing import Iterable

from .models import Habit


def _start_of_week(d: date) -> date:
    """Pondělí daného týdne"""
    return d - timedelta(days=d.weekday())


def calc_daily_streak(dates: Iterable[date], start_date: date | None = None) -> int:
    """
    Spočítá délku aktuálního denního streaku ke dni `start_date` (včetně).
    Streak = kolik po sobě jdoucích dní zpět existuje záznam.
    """

    if start_date is None:
        start_date = date.today()

    s = set(dates)
    day_to_check = start_date
    streak = 0
    while day_to_check in s:
        streak += 1
        day_to_check -= timedelta(days=1)
    return streak


def calc_weekly_streak(
    dated_values: Iterable[tuple[date, int]],
    target_per_week: int,
    start_date: date | None = None,
) -> int:
    """
    Spočítá délku aktuálního týdenního streaku ke dni `start_date` (včetně).
    Týden je započtený, pokud součet value v ISO týdnu >= target_per_week.
    Streak = počet po sobě jdoucích týdnů splněných od aktuálního týdne zpět.
    """

    if start_date is None:
        start_date = date.today()

    # agreagace hodnot po týdench (klíč = pondělí týdne)
    totals_by_week = defaultdict(int)
    for day, value in dated_values:
        totals_by_week[_start_of_week(day)] += int(value)

    streak = 0
    week_start = _start_of_week(start_date)
    while totals_by_week.get(week_start, 0) >= target_per_week:
        streak += 1
        week_start -= timedelta(days=7)
    return streak


def get_current_streak(habit: Habit, start_date: date | None = None) -> int:
    """
    Vrátí aktuální streak pro zadaný habit dle jeho periodicity.
    DAILY: po dnech (přítomnost záznamu = splnění).
    WEEKLY: po týdnech (součet value v týdnu >= target_per_period).
    """

    if start_date is None:
        start_date = date.today()

    queryset = habit.logs.filter(date__lte=start_date)

    # Periodicita Weekly
    if habit.periodicity == Habit.Periodicity.WEEKLY:
        pairs = queryset.values_list("date", "value")
        return calc_weekly_streak(pairs, habit.target_per_period, start_date=start_date)

    # Periodicita Daily (default)
    dates = queryset.values_list("date", flat=True)
    return calc_daily_streak(dates, start_date=start_date)
