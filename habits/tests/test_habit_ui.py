import pytest
from django.test import Client
from .factories import UserFactory
from habits.models import Habit

@pytest.mark.django_db
def test_habit_create_edit_delete_flow():
    u = UserFactory()
    c = Client(); c.force_login(u)

    # create
    r = c.post("/habits/new/", {
        "name": "Čtení",
        "periodicity": "daily",
        "target_per_period": 1
    })
    assert r.status_code in (302, 303)

    # list
    r = c.get("/habits/")
    assert r.status_code == 200
    assert "Čtení" in r.content.decode()

    # edit
    h_id = Habit.objects.filter(user=u).values_list("id", flat=True).first()
    assert h_id is not None
    r = c.post(f"/habits/{h_id}/edit/", {
        "name": "Čtení 20 min",
        "periodicity": "daily",
        "target_per_period": 1
    })
    assert r.status_code in (302, 303)

    # delete
    r = c.post(f"/habits/{h_id}/delete/")
    assert r.status_code in (302, 303)
