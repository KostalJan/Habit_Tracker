import datetime as dt

import pytest
from freezegun import freeze_time

from habits.services import (calc_daily_streak, calc_weekly_streak,
                             get_current_streak)

from .factories import HabitFactory, HabitLogFactory


@pytest.mark.django_db
def test_calc_daily_streak_basic_gap():
    # Bez freeze_time, používá se explicitní start_date
    start_date = dt.date(2025, 8, 13)
    dates = {
        start_date,  # 13.
        start_date - dt.timedelta(days=1),  # 12.
        start_date - dt.timedelta(days=2),  # 11.
    }
    assert calc_daily_streak(dates, start_date=start_date) == 3

    # s dírou (chybí 12.), streak jen 1
    dates_with_gap = {
        start_date,
        start_date - dt.timedelta(days=2),
    }
    assert calc_daily_streak(dates_with_gap, start_date=start_date) == 1


@pytest.mark.django_db
def test_calc_weekly_streak_reaching_targets():
    # Zafixování dneška kvůli větší čitelnosti weekly logiky.
    with freeze_time("2025-08-13"):
        today = dt.date.today()
        monday = today - dt.timedelta(days=today.weekday())  # pondělí aktuálního týdne

        # Pairs = (date, value), target = 3 splnění/týden
        pairs = []
        # aktuální týden: 3 splnění
        pairs += [(monday + dt.timedelta(days=i), 1) for i in (0, 2, 4)]
        # minulý týden: 3 splnění
        prev_monday = monday - dt.timedelta(days=7)
        pairs += [(prev_monday + dt.timedelta(days=i), 1) for i in (0, 1, 2)]
        # týden předtím: jen 1 splnění -> zde se streak zastaví
        prev2_monday = prev_monday - dt.timedelta(days=7)
        pairs += [(prev2_monday + dt.timedelta(days=3), 1)]

        assert calc_weekly_streak(pairs, target_per_week=3) == 2


@pytest.mark.django_db
def test_get_current_streak_daily_habit():
    with freeze_time("2025-08-13"):
        h = HabitFactory(periodicity="daily")
        today = dt.date.today()
        HabitLogFactory(habit=h, date=today)
        HabitLogFactory(habit=h, date=today - dt.timedelta(days=1))
        HabitLogFactory(habit=h, date=today - dt.timedelta(days=2))
        assert get_current_streak(h) == 3

        # Vložíme mezeru jednoho dne a ověříme, že streak spadne na 1
        HabitLogFactory(habit=h, date=today - dt.timedelta(days=4))
        assert (
            get_current_streak(h) == 3
        )  # stále 3 (4 dny zpět je mimo kontinuální řadu)
        # Smažeme log včerejška a zůstane jen dnešní -> streak 1
        h.logs.filter(date=today - dt.timedelta(days=1)).delete()
        assert get_current_streak(h) == 1


@pytest.mark.django_db
def test_get_current_streak_weekly_habit():
    with freeze_time("2025-08-13"):
        h = HabitFactory(periodicity="weekly", target_per_period=3)
        today = dt.date.today()
        monday = today - dt.timedelta(days=today.weekday())
        prev_monday = monday - dt.timedelta(days=7)
        prev2_monday = monday - dt.timedelta(days=14)

        # aktuální týden: 3 splnění
        for i in (0, 1, 2):
            HabitLogFactory(habit=h, date=monday + dt.timedelta(days=i), value=1)

        # minulý týden: 3 splnění
        for i in (0, 1, 2):
            HabitLogFactory(habit=h, date=prev_monday + dt.timedelta(days=i), value=1)

        # týden předtím: 1 splnění (streak se zastaví na 2)
        HabitLogFactory(habit=h, date=prev2_monday + dt.timedelta(days=3), value=1)

        assert get_current_streak(h) == 2
