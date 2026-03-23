from unittest.mock import patch

from django.test import override_settings

from django_fly_replay.services import (
    _build_serverless_config,
    get_or_create_serverless_machine,
)


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
