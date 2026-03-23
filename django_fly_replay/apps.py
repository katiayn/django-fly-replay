from django.apps import AppConfig


class DjangoFlyReplayConfig(AppConfig):
    name = "django_fly_replay"

    def ready(self):
        from django_fly_replay.decorators import _registry

        if _registry:
            print("Registered @fly_replay views:")
            for view in _registry:
                print(f"  {view.__module__}.{view.__qualname__}")
