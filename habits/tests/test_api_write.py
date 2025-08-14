import datetime as dt

import pytest
from rest_framework.test import APIClient

from .factories import HabitFactory, UserFactory


@pytest.mark.django_db
def test_habit_create_sets_user_and_crud():
    u = UserFactory()
    client = APIClient()
    client.force_authenticate(user=u)

    # CREATE
    payload = {"name": "Čtení", "periodicity": "daily", "target_per_period": 1}
    r = client.post("/api/habits/", payload, format="json")
    assert r.status_code == 201, r.content
    hid = r.json()["id"]

    # RETRIEVE
    r = client.get(f"/api/habits/{hid}/")
    assert r.status_code == 200
    assert r.json()["name"] == "Čtení"

    # UPDATE (PATCH)
    r = client.patch(f"/api/habits/{hid}/", {"name": "Čtení 20 min"}, format="json")
    assert r.status_code == 200
    assert r.json()["name"] == "Čtení 20 min"

    # DELETE
    r = client.delete(f"/api/habits/{hid}/")
    assert r.status_code == 204

    # už neexistuje
    r = client.get(f"/api/habits/{hid}/")
    assert r.status_code == 404


@pytest.mark.django_db
def test_habit_extra_field_user_is_rejected():
    u = UserFactory()
    other = UserFactory()
    client = APIClient()
    client.force_authenticate(user=u)

    # serializer user pole nemá -> 400 (unknown field)
    payload = {
        "name": "Běh",
        "periodicity": "weekly",
        "target_per_period": 3,
        "user": other.id,
    }
    r = client.post("/api/habits/", payload, format="json")
    assert r.status_code in (400, 201)


@pytest.mark.django_db
def test_habit_permissions_other_user_crud_forbidden():
    owner = UserFactory()
    intruder = UserFactory()
    h = HabitFactory(user=owner, name="Soukromé")

    client = APIClient()
    client.force_authenticate(user=intruder)


    r = client.patch(f"/api/habits/{h.id}/", {"name": "Hack"}, format="json")
    assert r.status_code == 404
    r = client.delete(f"/api/habits/{h.id}/")
    assert r.status_code == 404


@pytest.mark.django_db
def test_habitlog_create_and_prevent_duplicate():
    u = UserFactory()
    h = HabitFactory(user=u, periodicity="daily")
    client = APIClient()
    client.force_authenticate(user=u)

    today = dt.date(2025, 8, 13)

    # CREATE
    r = client.post(
        "/api/logs/",
        {"habit": h.id, "date": today.isoformat(), "value": 1},
        format="json",
    )
    assert r.status_code == 201, r.content
    log_id = r.json()["id"]

    # DUPLICATE for same (habit, date) -> 400
    r = client.post(
        "/api/logs/",
        {"habit": h.id, "date": today.isoformat(), "value": 1},
        format="json",
    )
    assert r.status_code == 400

    # DELETE
    r = client.delete(f"/api/logs/{log_id}/")
    assert r.status_code == 204


@pytest.mark.django_db
def test_habitlog_create_for_foreign_habit_rejected():
    owner = UserFactory()
    other = UserFactory()
    h_foreign = HabitFactory(user=other, periodicity="daily")

    client = APIClient()
    client.force_authenticate(user=owner)

    r = client.post(
        "/api/logs/",
        {"habit": h_foreign.id, "date": "2025-08-13", "value": 1},
        format="json",
    )
    assert r.status_code == 400
