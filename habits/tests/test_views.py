import pytest
from django.test import Client

from .factories import UserFactory


@pytest.mark.django_db
def test_today_requires_login():
    client = Client()
    r = client.get("/today/")
    assert r.status_code in (302, 301)  # redirect na login


@pytest.mark.django_db
def test_stats_page_requires_login():
    client = Client()
    r = client.get("/stats/")
    assert r.status_code in (302, 301)


@pytest.mark.django_db
def test_today_ok_when_logged_in():
    u = UserFactory()
    client = Client()
    client.force_login(u)
    r = client.get("/today/")
    assert r.status_code == 200


@pytest.mark.django_db
def test_stats_page_ok_when_logged_in():
    u = UserFactory()
    client = Client()
    client.force_login(u) 
    r = client.get("/stats/")
    assert r.status_code == 200
