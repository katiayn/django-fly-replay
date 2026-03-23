from unittest.mock import MagicMock, patch

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings

from django_fly_replay.client import _get_setting
from django_fly_replay.exceptions import FlyApiError
from django_fly_replay.machines import list_machines

from tests.conftest import _make_response


# --- _get_setting ---


@override_settings(FLY_APP_NAME="settings-app-name")
def test_get_setting_reads_django_settings():
    assert _get_setting("FLY_APP_NAME") == "settings-app-name"


def test_get_setting_falls_back_to_env(monkeypatch):
    monkeypatch.setenv("FLY_APP_NAME", "env-app-name")
    with override_settings():
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


@override_settings(FLY_APP_NAME="fly-app", FLY_API_TOKEN="fly-token", FLY_API_TIMEOUT="5")
def test_list_machines_calls_correct_endpoint():
    with patch("urllib.request.urlopen", return_value=_make_response([])) as mock_open:
        result = list_machines()
    assert result == []
    url = mock_open.call_args[0][0].full_url
    assert "/apps/fly-app/machines" in url
    assert mock_open.call_args[0][0].get_method() == "GET"


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


@override_settings(FLY_APP_NAME="fly-app", FLY_API_TOKEN="fly-token", FLY_API_TIMEOUT="5")
def test_api_request_custom_timeout_overrides_setting():
    from django_fly_replay.machines import wait_for_machine

    with patch("urllib.request.urlopen", return_value=_make_response({})) as mock_open:
        wait_for_machine("fly-machine-id", "destroyed", timeout=60)
    assert mock_open.call_args[1]["timeout"] == 60


@override_settings(FLY_APP_NAME="fly-app", FLY_API_TOKEN="fly-token", FLY_API_TIMEOUT="5")
def test_api_request_returns_none_on_empty_response():
    from django_fly_replay.machines import get_machine

    mock = MagicMock()
    mock.__enter__ = MagicMock(return_value=mock)
    mock.__exit__ = MagicMock(return_value=False)
    mock.read.return_value = b""
    with patch("urllib.request.urlopen", return_value=mock):
        assert get_machine("fly-machine-id") is None


@override_settings(FLY_APP_NAME="fly-app", FLY_API_TOKEN="fly-token", FLY_API_TIMEOUT="5")
def test_api_request_returns_none_on_invalid_json():
    from django_fly_replay.machines import get_machine

    mock = MagicMock()
    mock.__enter__ = MagicMock(return_value=mock)
    mock.__exit__ = MagicMock(return_value=False)
    mock.read.return_value = b"not json"
    with patch("urllib.request.urlopen", return_value=mock):
        assert get_machine("fly-machine-id") is None
