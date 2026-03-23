import os

from django.http import HttpResponse
from django.urls import resolve, Resolver404

from django_fly_replay.decorators import is_fly_replay
from django_fly_replay.services import get_or_create_serverless_machine


class FlyReplayMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.is_serverless = os.environ.get("IS_FLY_MACHINE_SERVERLESS") == "true"

    def __call__(self, request):
        try:
            match = resolve(request.path_info)
        except Resolver404:
            return self.get_response(request)

        view_func = match.func
        if hasattr(view_func, "view_class"):
            should_replay = is_fly_replay(view_func.view_class)
        else:
            should_replay = is_fly_replay(view_func)

        if self.is_serverless:
            if not should_replay:
                response = HttpResponse(status=200)
                response["fly-replay"] = "elsewhere=true"
                return response
        else:
            if should_replay:
                serverless_machine = get_or_create_serverless_machine()
                response = HttpResponse(status=200)
                response["fly-replay"] = f"instance={serverless_machine['id']}"
                return response

        return self.get_response(request)
