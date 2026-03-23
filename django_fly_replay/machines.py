from django_fly_replay.client import _api_request


def list_machines() -> list[dict]:
    return _api_request("GET", "/machines?include_deleted=false") or []


def get_machine(machine_id: str) -> dict:
    return _api_request("GET", f"/machines/{machine_id}")


def create_machine(config: dict) -> dict:
    return _api_request("POST", "/machines", body=config)


def start_machine(machine_id: str) -> None:
    _api_request("POST", f"/machines/{machine_id}/start")


def stop_machine(machine_id: str) -> None:
    _api_request("POST", f"/machines/{machine_id}/stop")


def destroy_machine(machine_id: str, force: bool = False) -> None:
    _api_request("DELETE", f"/machines/{machine_id}?force={'true' if force else 'false'}")


def wait_for_machine(machine_id: str, state: str, timeout: int | None = None) -> None:
    path = f"/machines/{machine_id}/wait?state={state}"
    if timeout is not None:
        path += f"&timeout={timeout}"
    _api_request("GET", path, timeout=timeout)
