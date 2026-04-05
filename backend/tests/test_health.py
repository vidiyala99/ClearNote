import importlib
import warnings

from fastapi.testclient import TestClient


def test_health_returns_ok(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "0.1.0"}


def test_app_import_emits_no_startup_deprecation_warning():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", DeprecationWarning)
        module = importlib.import_module("app.main")
        importlib.reload(module)

    messages = [str(item.message) for item in caught]
    assert not any("on_event is deprecated" in message for message in messages)
