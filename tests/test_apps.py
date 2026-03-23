from unittest.mock import patch

import django_fly_replay
from django_fly_replay.apps import DjangoFlyReplayConfig


def make_app_config():
    return DjangoFlyReplayConfig("django_fly_replay", django_fly_replay)


def test_ready_prints_registered_views(capsys):
    app_config = make_app_config()
    app_config.ready()
    out = capsys.readouterr().out
    assert "Registered @fly_replay views:" in out
    assert "replay" in out.lower()


def test_ready_silent_when_no_views_registered(capsys):
    with patch("django_fly_replay.decorators._registry", set()):
        app_config = make_app_config()
        app_config.ready()
    assert capsys.readouterr().out == ""
