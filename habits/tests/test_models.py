import datetime as dt

import pytest
from django.db import IntegrityError

from .factories import HabitFactory, HabitLogFactory


@pytest.mark.django_db
def test_habit_name_required():
    # je zadáno jméno habit
    habit = HabitFactory.build(name="")
    with pytest.raises(Exception):
        # full clean vyhodí Validation error
        habit.full_clean()


@pytest.mark.django_db
def test_habitlog_unique_per_day():
    # jenom jeden log za den a habit
    h = HabitFactory()
    today = dt.date.today()
    HabitLogFactory(habit=h, date=today)
    with pytest.raises(IntegrityError):
        # dojde k porušení UniqueConstraint
        HabitLogFactory(habit=h, date=today)
