import json
from unittest.mock import patch

from django.test import override_settings

from django_fly_replay.machines import (
    create_machine,
    destroy_machine,
    get_machine,
    start_machine,
    stop_machine,
    wait_for_machine,
)
from tests.test_client import _make_response


# --- Individual machine API calls ---


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
def test_stop_machine_posts_to_stop_endpoint():
    with patch("urllib.request.urlopen", return_value=_make_response({})) as mock_open:
        stop_machine("fly-machine-id")
    url = mock_open.call_args[0][0].full_url
    assert "/machines/fly-machine-id/stop" in url
    assert mock_open.call_args[0][0].get_method() == "POST"


@override_settings(FLY_APP_NAME="fly-app", FLY_API_TOKEN="fly-token", FLY_API_TIMEOUT="5")
def test_destroy_machine_sends_delete_request():
    with patch("urllib.request.urlopen", return_value=_make_response({})) as mock_open:
        destroy_machine("fly-machine-id")
    req = mock_open.call_args[0][0]
    assert "/machines/fly-machine-id" in req.full_url
    assert req.get_method() == "DELETE"
    assert "force=false" in req.full_url


@override_settings(FLY_APP_NAME="fly-app", FLY_API_TOKEN="fly-token", FLY_API_TIMEOUT="5")
def test_destroy_machine_force_flag():
    with patch("urllib.request.urlopen", return_value=_make_response({})) as mock_open:
        destroy_machine("fly-machine-id", force=True)
    assert "force=true" in mock_open.call_args[0][0].full_url


@override_settings(FLY_APP_NAME="fly-app", FLY_API_TOKEN="fly-token", FLY_API_TIMEOUT="5")
def test_wait_for_machine_calls_correct_endpoint():
    with patch("urllib.request.urlopen", return_value=_make_response({})) as mock_open:
        wait_for_machine("fly-machine-id", "destroyed")
    url = mock_open.call_args[0][0].full_url
    assert "/machines/fly-machine-id/wait" in url
    assert "state=destroyed" in url


@override_settings(FLY_APP_NAME="fly-app", FLY_API_TOKEN="fly-token", FLY_API_TIMEOUT="5")
def test_wait_for_machine_includes_timeout_param():
    with patch("urllib.request.urlopen", return_value=_make_response({})) as mock_open:
        wait_for_machine("fly-machine-id", "destroyed", timeout=30)
    url = mock_open.call_args[0][0].full_url
    assert "timeout=30" in url
