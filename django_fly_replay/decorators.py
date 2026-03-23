from collections.abc import Callable

_registry: set[Callable] = set()


def fly_replay(view_func: Callable) -> Callable:
    view_func._fly_replay = True
    _registry.add(view_func)
    return view_func


def is_fly_replay(view_func: Callable) -> bool:
    return getattr(view_func, "_fly_replay", False)
