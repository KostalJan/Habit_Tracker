import json

from django.urls import reverse


def test_healthcheck(client):
    url = reverse("healthz")
    res = client.get(url)
    assert res.status_code == 200
    payload = json.loads(res.content)
    assert payload["status"] == "ok"
