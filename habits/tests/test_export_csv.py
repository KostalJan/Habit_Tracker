import datetime as dt

import pytest
from django.test import Client

from .factories import HabitFactory, HabitLogFactory, UserFactory


@pytest.mark.django_db
def test_export_csv_filters_and_headers_and_bom():
    u = UserFactory()
    h1 = HabitFactory(user=u, name="Čtení")
    h2 = HabitFactory(user=u, name="Běh")

    # h1 logy: 2025-08-12, 2025-08-13
    for d in (dt.date(2025, 8, 12), dt.date(2025, 8, 13)):
        HabitLogFactory(habit=h1, date=d, value=1)

    # h2 log mimo filtr
    HabitLogFactory(habit=h2, date=dt.date(2025, 8, 11), value=1)

    client = Client()
    client.force_login(u)

    url = f"/export/logs.csv?habit_id={h1.id}&date__gte=2025-08-12&date__lte=2025-08-13&ordering=date"
    r = client.get(url)

    assert r.status_code == 200
    assert r["Content-Type"].startswith("text/csv")
    assert "attachment; filename=\"logs.csv\"" in r["Content-Disposition"]

    # UTF-8 BOM na začátku
    content = r.content
    assert content.startswith(b"\xef\xbb\xbf")

    # Dekóduj se sig (odstraní BOM) a zkontroluj obsah
    text = content.decode("utf-8-sig").strip().splitlines()
    assert text[0] == "habit_id,habit_name,date,value"
    # Máme 2 řádky pro h1 v daném rozsahu
    assert len(text) == 1 + 2
    # Ověř, že datumy jsou ve správném pořadí
    assert text[1].endswith(",2025-08-12,1")
    assert text[2].endswith(",2025-08-13,1")


@pytest.mark.django_db
def test_export_requires_login():
    client = Client()
    r = client.get("/export/logs.csv")
    # redirect na login
    assert r.status_code in (301, 302)
