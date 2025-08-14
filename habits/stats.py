from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from typing import Iterable

from .models import Habit
from .services import calc_daily_streak, calc_weekly_streak


def _start_of_week(d: date) -> date:
    """Pondělí daného týdne (ISO)."""
    return d - timedelta(days=d.weekday())


def _iter_days(n: int, start_date: date) -> Iterable[date]:
    """Posledních n dní včetně start_date, od nejstaršího po nejnovější."""
    start = start_date - timedelta(days=n - 1)
    for i in range(n):
        yield start + timedelta(days=i)


# ------- streak: nejdelší řada (daily / weekly) -------

def longest_daily_streak(dates: set[date]) -> int:
    """Nejdelší sekvence po sobě jdoucích dní se záznamem."""
    if not dates:
        return 0
    s = set(dates)
    best = 0
    for d in s:
        # začátek sekvence = předchozí den chybí
        if d - timedelta(days=1) not in s:
            length = 1
            nxt = d + timedelta(days=1)
            while nxt in s:
                length += 1
                nxt += timedelta(days=1)
            best = max(best, length)
    return best


def longest_weekly_streak(week_sums: dict[date, int], target: int) -> int:
    """Nejdelší řada po sobě jdoucích *týdnů* dosažených (>= target)."""
    success_weeks = {wk for wk, total in week_sums.items() if total >= target}
    if not success_weeks:
        return 0
    best = 0
    for wk in success_weeks:
        # začátek sekvence = předchozí týden (wk-7d) není úspěšný
        if wk - timedelta(days=7) not in success_weeks:
            length = 0
            cur = wk
            while cur in success_weeks:
                length += 1
                cur += timedelta(days=7)
            best = max(best, length)
    return best


# ------- úspěšnost 7/30 -------

def success_ratio_daily(dates: Iterable[date], days: int, start_date: date) -> float:
    """Podíl dní v okně, které mají záznam (0..1)."""
    s = set(dates)
    hit = sum(1 for d in _iter_days(days, start_date) if d in s)
    return hit / float(days)


def success_ratio_weekly(
    dated_values: Iterable[tuple[date, int]], target_per_week: int, days: int, start_date: date
) -> float:
    """
    Podíl *týdnů* v okně, které splnily target (0..1).
    Speciálně pro malé okno (<14 dní) se hodnotí aktuální týden.
    """
    # agregace jen v rámci okna
    start = start_date - timedelta(days=days - 1)
    by_week = defaultdict(int)
    for d, v in dated_values:
        if start <= d <= start_date:
            by_week[_start_of_week(d)] += int(v)

    if days < 14:
        weeks = [_start_of_week(start_date)]
    else:
        start_week = _start_of_week(start)
        end_week = _start_of_week(start_date)
        weeks = []
        w = start_week
        while w <= end_week:
            weeks.append(w)
            w += timedelta(days=7)

    if not weeks:
        return 0.0

    achieved = sum(1 for w in weeks if by_week.get(w, 0) >= target_per_week)
    return achieved / float(len(weeks))


# ------- veřejné API služby -------

def compute_user_stats(user, start_date: date | None = None) -> list[dict]:
    """
    Vrátí seznam statistik pro všechny habit(y) uživatele.
    Každá položka: {id, name, periodicity, current_streak, longest_streak, success_7d, success_30d}
    """
    if start_date is None:
        start_date = date.today()

    out: list[dict] = []
    habits = Habit.objects.filter(user=user).order_by("id")

    for h in habits:
        logs_qs = h.logs.filter(date__lte=start_date)

        if h.periodicity == Habit.Periodicity.WEEKLY:
            pairs = list(logs_qs.values_list("date", "value"))
            # pro streaky se použijí všechny dostupné týdny (do start_date)
            week_sums_all = defaultdict(int)
            for d, v in pairs:
                week_sums_all[_start_of_week(d)] += int(v)

            current = calc_weekly_streak(pairs, h.target_per_period, start_date=start_date)
            longest = longest_weekly_streak(week_sums_all, h.target_per_period)
            success_7d = success_ratio_weekly(pairs, h.target_per_period, 7, start_date)
            success_30d = success_ratio_weekly(pairs, h.target_per_period, 30, start_date)
        else:
            dates = set(logs_qs.values_list("date", flat=True))
            current = calc_daily_streak(dates, start_date=start_date)
            longest = longest_daily_streak(dates)
            success_7d = success_ratio_daily(dates, 7, start_date)
            success_30d = success_ratio_daily(dates, 30, start_date)

        out.append(
            {
                "id": h.id,
                "name": h.name,
                "periodicity": h.periodicity,
                "current_streak": current,
                "longest_streak": longest,
                "success_7d": round(success_7d, 4),
                "success_30d": round(success_30d, 4),
            }
        )

    return out
