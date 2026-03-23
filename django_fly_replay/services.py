import os

from django_fly_replay.machines import create_machine, list_machines, start_machine

_SERVERLESS_TAG = "IS_FLY_MACHINE_SERVERLESS"
_STARTED_STATES = {"started"}
_STARTABLE_STATES = {"stopped", "suspended", "created"}


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
