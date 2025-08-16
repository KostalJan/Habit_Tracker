
import datetime as dt

import pytest
from django.test import Client

from .factories import HabitFactory, HabitLogFactory, UserFactory


@pytest.mark.django_db
def test_toggle_creates_and_deletes_today_log():
    u = UserFactory()
    h = HabitFactory(user=u, periodicity="daily")
    client = Client()
    client.force_login(u)

    today = dt.date.today()
    url = f"/today/toggle/{h.id}/"

    # 1) create
    r = client.post(url, HTTP_HX_REQUEST="true")
    assert r.status_code == 200
    assert "today-list" in r.content.decode()
    assert h.logs.filter(date=today).count() == 1

    # 2) delete (toggle again)
    r = client.post(url, HTTP_HX_REQUEST="true")
    assert r.status_code == 200
    assert h.logs.filter(date=today).count() == 0
