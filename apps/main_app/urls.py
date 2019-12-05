from django.conf.urls import url, include
from . import views

urlpatterns = [
    url(r'^parlayresults',views.parlayresults),
    url(r'^processparlay', views.processparlay),
    url(r'^parlay', views.parlay),
    url(r'^leaderboard', views.leaderboard),
    url(r'^walkthrough', views.walkthrough),
    url(r'^processlogin',views.processlogin),
    url(r'user',views.user),
    url(r'logout',views.logout),
    url(r'pick',views.process_bet),
    url(r'scores/(?P<gameid>\d+)', views.score),
    url(r'scores', views.scores),
    url(r'index', views.sportodds),
    url(r'register',views.register),
    url(r'^', views.login),
]