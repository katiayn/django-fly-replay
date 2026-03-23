import os
import shlex

from django_fly_replay.machines import create_machine


def _build_process_config(
    cmd: list[str],
    env: dict[str, str] | None = None,
    guest: dict | None = None,
) -> dict:
    image = os.environ["FLY_IMAGE_REF"]
    config: dict = {
        "config": {
            "image": image,
            "auto_destroy": True,
            "processes": [{"cmd": cmd}],
        }
    }
    if env:
        config["config"]["env"] = env
    if guest:
        config["config"]["guest"] = guest
    return config


def create_process_machine(
    cmd: list[str] | str,
    env: dict[str, str] | None = None,
    guest: dict | None = None,
) -> dict:
    if isinstance(cmd, str):
        cmd = shlex.split(cmd)
    config = _build_process_config(cmd, env=env, guest=guest)
    return create_machine(config)
