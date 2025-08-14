import datetime as dt

import pytest
from rest_framework.test import APIClient

from .factories import HabitFactory, HabitLogFactory, UserFactory


@pytest.mark.django_db
def test_user_sees_only_their_habits():
    u1, u2 = UserFactory(), UserFactory()
    h1 = HabitFactory(user=u1, name="Moje")
    HabitFactory(user=u2, name="Cizi")

    client = APIClient()
    client.force_authenticate(user=u1)

    res = client.get("/api/habits/")
    assert res.status_code == 200
    data = res.json()
    items = data.get("results", data)
    ids = {item["id"] for item in items}
    assert ids == {h1.id}


@pytest.mark.django_db
def test_user_cannot_retrieve_others_habit():
    u1, u2 = UserFactory(), UserFactory()
    HabitFactory(user=u1, name="Moje")
    foreign = HabitFactory(user=u2, name="Cizi")

    client = APIClient()
    client.force_authenticate(user=u1)

    res = client.get(f"/api/habits/{foreign.id}/")
    # díky filtrování přes get_queryset "neexistuje" => 404
    assert res.status_code == 404


@pytest.mark.django_db
def test_logs_filtering_by_habit_and_date_range_and_ordering():
    u = UserFactory()
    h1 = HabitFactory(user=u)
    h2 = HabitFactory(user=u)

    # data pro h1: 2025-08-10, 12, 13
    d1 = dt.date(2025, 8, 10)
    d2 = dt.date(2025, 8, 12)
    d3 = dt.date(2025, 8, 13)
    for d in (d1, d2, d3):
        HabitLogFactory(habit=h1, date=d, value=1)

    # data pro h2: mimo filtr
    HabitLogFactory(habit=h2, date=dt.date(2025, 8, 9), value=1)

    client = APIClient()
    client.force_authenticate(user=u)

    res = client.get(
        f"/api/logs/?habit_id={h1.id}&date__gte=2025-08-12&date__lte=2025-08-13&ordering=date"
    )
    assert res.status_code == 200
    data = res.json()
    items = data.get("results", data)
    got_dates = [item["date"] for item in items]
    assert got_dates == ["2025-08-12", "2025-08-13"]
