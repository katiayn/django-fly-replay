from django.test import RequestFactory

from django_fly_replay.decorators import is_fly_replay
from tests.views import PlainCBV, ReplayCBV, plain_view, replay_view


def test_decorated_view_is_recognized():
    assert is_fly_replay(replay_view) is True


def test_plain_view_is_not_recognized():
    assert is_fly_replay(plain_view) is False


def test_decorated_cbv_is_recognized():
    assert is_fly_replay(ReplayCBV) is True


def test_plain_cbv_is_not_recognized():
    assert is_fly_replay(PlainCBV) is False


def test_decorator_does_not_alter_view_behavior():
    request = RequestFactory().get("/")
    assert replay_view(request).content == b"replay"
