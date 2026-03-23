import json
from unittest.mock import MagicMock, patch

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings

from django_fly_replay.machines import (
    FlyApiError,
    _build_serverless_config,
    _get_setting,
    create_machine,
    get_machine,
    get_or_create_serverless_machine,
    list_machines,
    start_machine,
)


# --- _get_setting ---


@override_settings(FLY_APP_NAME="settings-app-name")
def test_get_setting_reads_django_settings():
    assert _get_setting("FLY_APP_NAME") == "settings-app-name"


def test_get_setting_falls_back_to_env(monkeypatch):
    monkeypatch.setenv("FLY_APP_NAME", "env-app-name")
    with override_settings():
        # ensure it's not in Django settings
        from django.conf import settings

        if hasattr(settings, "FLY_APP_NAME"):
            delattr(settings, "FLY_APP_NAME")
        assert _get_setting("FLY_APP_NAME") == "env-app-name"


def test_get_setting_returns_default_when_missing(monkeypatch):
    monkeypatch.delenv("FLY_API_TIMEOUT", raising=False)
    assert _get_setting("FLY_API_TIMEOUT", default="10") == "10"


def test_get_setting_raises_when_missing_and_no_default(monkeypatch):
    monkeypatch.delenv("FLY_APP_NAME", raising=False)
    with override_settings():
        from django.conf import settings

        if hasattr(settings, "FLY_APP_NAME"):
            delattr(settings, "FLY_APP_NAME")
        with pytest.raises(ImproperlyConfigured):
            _get_setting("FLY_APP_NAME")


# --- _api_request (via public functions) ---


def _make_response(body: dict | list, status: int = 200):
    raw = json.dumps(body).encode()
    mock = MagicMock()
    mock.__enter__ = MagicMock(return_value=mock)
    mock.__exit__ = MagicMock(return_value=False)
    mock.read.return_value = raw
    mock.status = status
    return mock


@override_settings(FLY_APP_NAME="fly-app", FLY_API_TOKEN="fly-token", FLY_API_TIMEOUT="5")
def test_list_machines_calls_correct_endpoint():
    with patch("urllib.request.urlopen", return_value=_make_response([])) as mock_open:
        result = list_machines()
    assert result == []
    url = mock_open.call_args[0][0].full_url
    assert "/apps/fly-app/machines" in url
    assert mock_open.call_args[0][0].get_method() == "GET"


@override_settings(FLY_APP_NAME="fly-app", FLY_API_TOKEN="fly-token", FLY_API_TIMEOUT="5")
def test_get_machine_calls_correct_endpoint():
    machine = {"id": "fly-machine-id", "state": "started"}
    with patch(
        "urllib.request.urlopen", return_value=_make_response(machine)
    ) as mock_open:
        result = get_machine("fly-machine-id")
    assert result == machine
    url = mock_open.call_args[0][0].full_url
    assert "/machines/fly-machine-id" in url


@override_settings(FLY_APP_NAME="fly-app", FLY_API_TOKEN="fly-token", FLY_API_TIMEOUT="5")
def test_create_machine_posts_config():
    created = {"id": "fly-machine-id", "state": "created"}
    config = {"config": {"image": "registry.fly.io/fly-app:deployment-123test"}}
    with patch(
        "urllib.request.urlopen", return_value=_make_response(created)
    ) as mock_open:
        result = create_machine(config)
    assert result == created
    req = mock_open.call_args[0][0]
    assert req.get_method() == "POST"
    assert json.loads(req.data) == config


@override_settings(FLY_APP_NAME="fly-app", FLY_API_TOKEN="fly-token", FLY_API_TIMEOUT="5")
def test_start_machine_posts_to_start_endpoint():
    with patch("urllib.request.urlopen", return_value=_make_response({})) as mock_open:
        start_machine("fly-machine-id")
    url = mock_open.call_args[0][0].full_url
    assert "/machines/fly-machine-id/start" in url
    assert mock_open.call_args[0][0].get_method() == "POST"


@override_settings(FLY_APP_NAME="fly-app", FLY_API_TOKEN="fly-token", FLY_API_TIMEOUT="5")
def test_api_request_raises_fly_api_error_on_http_error():
    import urllib.error

    error = urllib.error.HTTPError(
        url="http://flymachines.io",
        code=401,
        msg="Unauthorized",
        hdrs=None,
        fp=MagicMock(read=lambda: b"bad token"),
    )
    with patch("urllib.request.urlopen", side_effect=error):
        with pytest.raises(FlyApiError) as exc_info:
            list_machines()
    assert exc_info.value.status_code == 401


# --- _build_serverless_config ---


def test_build_serverless_config_includes_image(monkeypatch):
    monkeypatch.setenv("FLY_IMAGE_REF", "registry.fly.io/fly-app:deployment-123")
    config = _build_serverless_config()
    assert config["config"]["image"] == "registry.fly.io/fly-app:deployment-123"


def test_build_serverless_config_tags_env(monkeypatch):
    monkeypatch.setenv("FLY_IMAGE_REF", "registry.fly.io/fly-app:deployment-123")
    config = _build_serverless_config()
    assert config["config"]["env"]["IS_FLY_MACHINE_SERVERLESS"] == "true"


def test_build_serverless_config_sets_autostop(monkeypatch):
    monkeypatch.setenv("FLY_IMAGE_REF", "registry.fly.io/fly-app:deployment-123")
    config = _build_serverless_config()
    service = config["config"]["services"][0]
    assert service["autostop"] == "stop"


# --- get_or_create_serverless_machine ---

SERVERLESS_ENV = {"IS_FLY_MACHINE_SERVERLESS": "true"}


@override_settings(FLY_APP_NAME="fly-app", FLY_API_TOKEN="fly-token", FLY_API_TIMEOUT="5")
def test_get_or_create_returns_started_machine():
    started = {"id": "started-fly-machine-id", "state": "started", "config": {"env": SERVERLESS_ENV}}
    with patch(
        "django_fly_replay.machines._api_request", return_value=[started]
    ) as mock_req:
        result = get_or_create_serverless_machine()
    assert result == started
    mock_req.assert_called_once_with("GET", "/machines?include_deleted=false")


@override_settings(FLY_APP_NAME="fly-app", FLY_API_TOKEN="fly-token", FLY_API_TIMEOUT="5")
def test_get_or_create_starts_stopped_machine():
    stopped = {"id": "stopped-fly-machine-id", "state": "stopped", "config": {"env": SERVERLESS_ENV}}
    with patch("django_fly_replay.machines._api_request") as mock_req:
        mock_req.side_effect = [[stopped], None]
        result = get_or_create_serverless_machine()
    assert result == stopped
    mock_req.assert_any_call("POST", "/machines/stopped-fly-machine-id/start")


@override_settings(FLY_APP_NAME="fly-app", FLY_API_TOKEN="fly-token", FLY_API_TIMEOUT="5")
def test_get_or_create_starts_suspended_machine():
    suspended = {"id": "suspended-fly-machine-id", "state": "suspended", "config": {"env": SERVERLESS_ENV}}
    with patch("django_fly_replay.machines._api_request") as mock_req:
        mock_req.side_effect = [[suspended], None]
        result = get_or_create_serverless_machine()
    assert result == suspended
    mock_req.assert_any_call("POST", "/machines/suspended-fly-machine-id/start")


@override_settings(FLY_APP_NAME="fly-app", FLY_API_TOKEN="fly-token", FLY_API_TIMEOUT="5")
def test_get_or_create_creates_when_none_found(monkeypatch):
    monkeypatch.setenv("FLY_IMAGE_REF", "registry.fly.io/fly-app:deployment-123")
    new_machine = {"id": "fly-machine-id", "state": "created", "config": {"env": SERVERLESS_ENV}}
    with patch("django_fly_replay.machines._api_request") as mock_req:
        mock_req.side_effect = [[], new_machine]
        result = get_or_create_serverless_machine()
    assert result == new_machine
    create_call = mock_req.call_args_list[1]
    assert create_call[0][0] == "POST"
    assert create_call[0][1] == "/machines"


@override_settings(FLY_APP_NAME="fly-app", FLY_API_TOKEN="fly-token", FLY_API_TIMEOUT="5")
def test_get_or_create_skips_transitional_machines(monkeypatch):
    monkeypatch.setenv("FLY_IMAGE_REF", "registry.fly.io/fly-app:deployment-123")
    destroying = {"id": "destroyed-fly-machine-id", "state": "destroying", "config": {"env": SERVERLESS_ENV}}
    new_machine = {"id": "new-fly-machine-id", "state": "created"}
    with patch("django_fly_replay.machines._api_request") as mock_req:
        mock_req.side_effect = [[destroying], new_machine]
        get_or_create_serverless_machine()
    # should not have called the start endpoint on the destroying machine
    called_paths = [c[0][1] for c in mock_req.call_args_list]
    assert "/machines/destroyed-fly-machine-id/start" not in called_paths


@override_settings(FLY_APP_NAME="fly-app", FLY_API_TOKEN="fly-token", FLY_API_TIMEOUT="5")
def test_get_or_create_ignores_non_serverless_machines(monkeypatch):
    monkeypatch.setenv("FLY_IMAGE_REF", "registry.fly.io/fly-app:deployment-123")
    plain = {"id": "plain-fly-machine-id", "state": "started", "config": {"env": {}}}
    new_machine = {"id": "new-fly-machine-id"}
    with patch("django_fly_replay.machines._api_request") as mock_req:
        mock_req.side_effect = [[plain], new_machine]
        result = get_or_create_serverless_machine()
    assert result == new_machine
