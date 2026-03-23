import json
import os
import urllib.error
import urllib.request

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

_BASE_URL = "https://api.machines.dev/v1"

_SERVERLESS_TAG = "IS_FLY_MACHINE_SERVERLESS"
_STARTED_STATES = {"started"}
_STARTABLE_STATES = {"stopped", "suspended", "created"}


class FlyApiError(Exception):
    def __init__(self, status_code: int, url: str, body: str):
        self.status_code = status_code
        self.url = url
        self.body = body
        super().__init__(f"Fly API {status_code} for {url}: {body}")


def _get_setting(name: str, default: str | None = None) -> str:
    value = getattr(settings, name, None) or os.environ.get(name) or default
    if value is None:
        raise ImproperlyConfigured(
            f"Set {name} in Django settings or as an environment variable."
        )
    return value


def _get_app_name() -> str:
    return _get_setting("FLY_APP_NAME")


def _get_api_token() -> str:
    return _get_setting("FLY_API_TOKEN")


def _get_timeout() -> int:
    return int(_get_setting("FLY_API_TIMEOUT", default="10"))


def _api_request(
    method: str, path: str, body: dict | None = None
) -> dict | list | None:
    app_name = _get_app_name()
    token = _get_api_token()
    timeout = _get_timeout()

    url = f"{_BASE_URL}/apps/{app_name}{path}"
    data = json.dumps(body).encode("utf-8") if body is not None else None

    request = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
            if not raw:
                return None
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return None
    except urllib.error.HTTPError as exc:
        body_text = exc.read().decode("utf-8", errors="replace")
        raise FlyApiError(exc.code, url, body_text) from exc


def _build_serverless_config() -> dict:
    # FLY_IMAGE_REF is injected by Fly at runtime — always present on a Fly machine.
    image = os.environ["FLY_IMAGE_REF"]
    return {
        "config": {
            "image": image,
            "env": {_SERVERLESS_TAG: "true"},
            "services": [
                {
                    "protocol": "tcp",
                    "internal_port": 8000,
                    "autostop": "stop",
                    "autostart": True,
                    "ports": [
                        {"port": 443, "handlers": ["tls", "http"]},
                        {"port": 80, "handlers": ["http"]},
                    ],
                }
            ],
        }
    }


def list_machines() -> list[dict]:
    return _api_request("GET", "/machines?include_deleted=false") or []


def get_machine(machine_id: str) -> dict:
    return _api_request("GET", f"/machines/{machine_id}")


def create_machine(config: dict) -> dict:
    return _api_request("POST", "/machines", body=config)


def start_machine(machine_id: str) -> None:
    _api_request("POST", f"/machines/{machine_id}/start")


def get_or_create_serverless_machine() -> dict:
    for machine in list_machines():
        env = machine.get("config", {}).get("env", {})
        if env.get(_SERVERLESS_TAG) != "true":
            continue

        state = machine.get("state", "")

        if state in _STARTED_STATES:
            return machine

        if state in _STARTABLE_STATES:
            start_machine(machine["id"])
            return machine

        # Skip machines in transitional/terminal states ("starting", "destroying", etc.)

    return create_machine(_build_serverless_config())
