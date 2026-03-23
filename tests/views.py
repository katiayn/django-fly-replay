from django.http import HttpResponse

from django_fly_replay import fly_replay


def plain_view(request):
    return HttpResponse("plain")


@fly_replay
def replay_view(request):
    return HttpResponse("replay")


class PlainCBV:
    @classmethod
    def as_view(cls):
        def view(request):
            return HttpResponse("cbv-plain")

        view.view_class = cls
        return view


@fly_replay
class ReplayCBV:
    @classmethod
    def as_view(cls):
        def view(request):
            return HttpResponse("cbv-replay")

        view.view_class = cls
        return view
