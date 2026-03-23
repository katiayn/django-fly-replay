import pytest
from unittest.mock import patch

from django.test import RequestFactory

from django_fly_replay.exceptions import FlyApiError
from django_fly_replay.middleware import FlyReplayMiddleware

MACHINE = {"id": "fly-machine-id"}


def get_response(request):
    from django.http import HttpResponse

    return HttpResponse("ok")


def make_middleware(is_serverless=False):
    with patch.dict(
        "os.environ", {"IS_FLY_MACHINE_SERVERLESS": "true" if is_serverless else ""}
    ):
        return FlyReplayMiddleware(get_response)


factory = RequestFactory()


# --- Main machine (not serverless) ---


@pytest.mark.django_db
def test_main_machine_replays_fly_replay_view():
    middleware = make_middleware(is_serverless=False)
    request = factory.get("/replay/")
    with patch(
        "django_fly_replay.middleware.get_or_create_serverless_machine",
        return_value=MACHINE,
    ):
        response = middleware(request)
    assert response["fly-replay"] == f"instance={MACHINE['id']}"


@pytest.mark.django_db
def test_main_machine_passes_through_plain_view():
    middleware = make_middleware(is_serverless=False)
    request = factory.get("/plain/")
    with patch(
        "django_fly_replay.middleware.get_or_create_serverless_machine"
    ) as mock_machine:
        response = middleware(request)
    mock_machine.assert_not_called()
    assert "fly-replay" not in response


@pytest.mark.django_db
def test_main_machine_passes_through_unresolvable_url():
    middleware = make_middleware(is_serverless=False)
    request = factory.get("/does-not-exist/")
    with patch(
        "django_fly_replay.middleware.get_or_create_serverless_machine"
    ) as mock_machine:
        response = middleware(request)
    mock_machine.assert_not_called()
    assert response.status_code == 200


# --- Serverless machine ---


@pytest.mark.django_db
def test_serverless_machine_passes_through_fly_replay_view():
    middleware = make_middleware(is_serverless=True)
    request = factory.get("/replay/")
    response = middleware(request)
    assert "fly-replay" not in response
    assert response.status_code == 200


@pytest.mark.django_db
def test_serverless_machine_bounces_plain_view():
    middleware = make_middleware(is_serverless=True)
    request = factory.get("/plain/")
    response = middleware(request)
    assert response["fly-replay"] == "elsewhere=true"


@pytest.mark.django_db
def test_serverless_machine_bounces_unresolvable_url():
    middleware = make_middleware(is_serverless=True)
    request = factory.get("/does-not-exist/")
    response = middleware(request)
    # Resolver404 is caught — falls through to get_response, no bounce
    assert "fly-replay" not in response


@pytest.mark.django_db
def test_main_machine_propagates_fly_api_error():
    middleware = make_middleware(is_serverless=False)
    request = factory.get("/replay/")
    with patch(
        "django_fly_replay.middleware.get_or_create_serverless_machine",
        side_effect=FlyApiError(500, "http://api.machines.dev", "internal error"),
    ):
        with pytest.raises(FlyApiError):
            middleware(request)


# --- Class-based views ---


@pytest.mark.django_db
def test_main_machine_replays_fly_replay_cbv():
    middleware = make_middleware(is_serverless=False)
    request = factory.get("/cbv-replay/")
    with patch(
        "django_fly_replay.middleware.get_or_create_serverless_machine",
        return_value=MACHINE,
    ):
        response = middleware(request)
    assert response["fly-replay"] == f"instance={MACHINE['id']}"


@pytest.mark.django_db
def test_main_machine_passes_through_plain_cbv():
    middleware = make_middleware(is_serverless=False)
    request = factory.get("/cbv-plain/")
    with patch(
        "django_fly_replay.middleware.get_or_create_serverless_machine"
    ) as mock_machine:
        response = middleware(request)
    mock_machine.assert_not_called()
    assert "fly-replay" not in response
