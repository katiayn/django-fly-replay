from django.urls import path

from tests import views

urlpatterns = [
    path("plain/", views.plain_view),
    path("replay/", views.replay_view),
    path("cbv-plain/", views.PlainCBV.as_view()),
    path("cbv-replay/", views.ReplayCBV.as_view()),
]
