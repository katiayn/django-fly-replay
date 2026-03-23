import json
from unittest.mock import patch

from django.test import override_settings

from django_fly_replay.processes import _build_process_config, create_process_machine
from tests.test_client import _make_response


# --- _build_process_config ---


def test_build_process_config_includes_image(monkeypatch):
    monkeypatch.setenv("FLY_IMAGE_REF", "registry.fly.io/fly-app:deployment-123")
    config = _build_process_config(["python", "manage.py", "migrate"])
    assert config["config"]["image"] == "registry.fly.io/fly-app:deployment-123"


def test_build_process_config_sets_auto_destroy(monkeypatch):
    monkeypatch.setenv("FLY_IMAGE_REF", "registry.fly.io/fly-app:deployment-123")
    config = _build_process_config(["python", "manage.py", "migrate"])
    assert config["config"]["auto_destroy"] is True


def test_build_process_config_sets_command(monkeypatch):
    monkeypatch.setenv("FLY_IMAGE_REF", "registry.fly.io/fly-app:deployment-123")
    cmd = ["python", "manage.py", "migrate"]
    config = _build_process_config(cmd)
    assert config["config"]["processes"][0]["cmd"] == cmd


def test_build_process_config_has_no_services(monkeypatch):
    monkeypatch.setenv("FLY_IMAGE_REF", "registry.fly.io/fly-app:deployment-123")
    config = _build_process_config(["python", "manage.py", "migrate"])
    assert "services" not in config["config"]


def test_build_process_config_includes_env_when_provided(monkeypatch):
    monkeypatch.setenv("FLY_IMAGE_REF", "registry.fly.io/fly-app:deployment-123")
    config = _build_process_config(["python", "manage.py", "migrate"], env={"FOO": "bar"})
    assert config["config"]["env"] == {"FOO": "bar"}


def test_build_process_config_omits_env_when_none(monkeypatch):
    monkeypatch.setenv("FLY_IMAGE_REF", "registry.fly.io/fly-app:deployment-123")
    config = _build_process_config(["python", "manage.py", "migrate"])
    assert "env" not in config["config"]


def test_build_process_config_includes_guest_when_provided(monkeypatch):
    monkeypatch.setenv("FLY_IMAGE_REF", "registry.fly.io/fly-app:deployment-123")
    guest = {"cpu_kind": "shared", "cpus": 2, "memory_mb": 512}
    config = _build_process_config(["python", "manage.py", "migrate"], guest=guest)
    assert config["config"]["guest"] == guest


# --- create_process_machine ---


@override_settings(FLY_APP_NAME="fly-app", FLY_API_TOKEN="fly-token", FLY_API_TIMEOUT="5")
def test_create_process_machine_with_list_cmd(monkeypatch):
    monkeypatch.setenv("FLY_IMAGE_REF", "registry.fly.io/fly-app:deployment-123")
    created = {"id": "proc-machine-id", "state": "created"}
    cmd = ["python", "manage.py", "migrate"]
    with patch("urllib.request.urlopen", return_value=_make_response(created)) as mock_open:
        result = create_process_machine(cmd)
    assert result == created
    body = json.loads(mock_open.call_args[0][0].data)
    assert body["config"]["processes"][0]["cmd"] == cmd
    assert body["config"]["auto_destroy"] is True


@override_settings(FLY_APP_NAME="fly-app", FLY_API_TOKEN="fly-token", FLY_API_TIMEOUT="5")
def test_create_process_machine_with_string_cmd(monkeypatch):
    monkeypatch.setenv("FLY_IMAGE_REF", "registry.fly.io/fly-app:deployment-123")
    created = {"id": "proc-machine-id", "state": "created"}
    with patch("urllib.request.urlopen", return_value=_make_response(created)) as mock_open:
        create_process_machine("python manage.py migrate")
    body = json.loads(mock_open.call_args[0][0].data)
    assert body["config"]["processes"][0]["cmd"] == ["python", "manage.py", "migrate"]


@override_settings(FLY_APP_NAME="fly-app", FLY_API_TOKEN="fly-token", FLY_API_TIMEOUT="5")
def test_create_process_machine_passes_env_and_guest(monkeypatch):
    monkeypatch.setenv("FLY_IMAGE_REF", "registry.fly.io/fly-app:deployment-123")
    created = {"id": "proc-machine-id", "state": "created"}
    env = {"DATABASE_URL": "postgres://..."}
    guest = {"cpu_kind": "shared", "cpus": 1, "memory_mb": 256}
    with patch("urllib.request.urlopen", return_value=_make_response(created)) as mock_open:
        create_process_machine(["python", "manage.py", "migrate"], env=env, guest=guest)
    body = json.loads(mock_open.call_args[0][0].data)
    assert body["config"]["env"] == env
    assert body["config"]["guest"] == guest
