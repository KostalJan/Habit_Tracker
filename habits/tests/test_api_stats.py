import datetime as dt

import pytest
from freezegun import freeze_time
from rest_framework.test import APIClient

from .factories import HabitFactory, HabitLogFactory, UserFactory


@pytest.mark.django_db
def test_stats_returns_daily_and_weekly_metrics():
    with freeze_time("2025-08-13"):  # středa
        u = UserFactory()
        client = APIClient()
        client.force_authenticate(user=u)

        # daily habit: záznamy poslední 3 dny (11,12,13)
        h_daily = HabitFactory(user=u, periodicity="daily", name="Čtení")
        for i in (0, 1, 2):
            HabitLogFactory(habit=h_daily, date=dt.date(2025, 8, 13) - dt.timedelta(days=i))

        # weekly habit: target=3, splněn tento i minulý týden, předešlý jen 1x
        h_week = HabitFactory(user=u, periodicity="weekly", target_per_period=3, name="Běh")
        # aktuální týden (Po 11.8., Út 12.8., St 13.8.)
        for d in (dt.date(2025, 8, 11), dt.date(2025, 8, 12), dt.date(2025, 8, 13)):
            HabitLogFactory(habit=h_week, date=d, value=1)
        # minulý týden (Po 4.8., Út 5.8., St 6.8.)
        for d in (dt.date(2025, 8, 4), dt.date(2025, 8, 5), dt.date(2025, 8, 6)):
            HabitLogFactory(habit=h_week, date=d, value=1)
        # týden předtím (Po 28.7.) jen 1x
        HabitLogFactory(habit=h_week, date=dt.date(2025, 7, 31), value=1)

        res = client.get("/api/stats/")
        assert res.status_code == 200
        payload = res.json()["habits"]

        # Pomocné mapování podle id
        by_id = {item["id"]: item for item in payload}

        d = by_id[h_daily.id]
        assert d["current_streak"] == 3
        assert d["longest_streak"] == 3
        # 7 dní okno: jen 3 hity ze 7 (11–13.8.) => ~0.4286
        assert abs(d["success_7d"] - (3 / 7)) < 1e-4
        # 30 dní okno: 3/30 => 0.1
        assert abs(d["success_30d"] - 0.1) < 1e-4

        w = by_id[h_week.id]
        assert w["current_streak"] == 2  # tento + minulý týden splněn
        assert w["longest_streak"] == 2  # nejdelší řada = 2
        # success_7d pro weekly hodnotíme jen aktuální týden => splněn
        assert w["success_7d"] == 1.0
        # posledních 30 dní pokrývá 5 týdnů (14.7., 21.7., 28.7., 4.8., 11.8.)
        # splněny 2 týdny => 2/5 = 0.4
        assert abs(w["success_30d"] - 0.4) < 1e-6
