from django.urls import path
from . import views
from .views import Matches

urlpatterns = [
    path('', views.homepage, name="homepage"),
    path('about/', views.about, name="about"),
    path('matches/', Matches.as_view(), name="matches"),
    path('matches/<uuid:pk>,', views.thismatch, name="thismatch"),
    path('makematch/', views.makematch, name='makematch'),
    path('creatematch/', views.creatematch, name='creatematch'),
    path('deletematch/<uuid:pk>', views.deletematch, name="deletematch"),
    path('createsets/<uuid:pk>', views.createsets, name='createsets'),
    path('thisset/<uuid:pk>', views.thisset, name="thisset"),
    path('deleteset/<uuid:pk>', views.deleteset, name="deleteset"),
    path('creategame/<uuid:pk>/<str:type>', views.creategame, name='creategame'),
    path('thisgame/<uuid:pk>', views.thisgame, name="thisgame"),
    path('deletegame/<uuid:pk>', views.deletegame, name="deletegame"),
    path('createpoint/<uuid:pk>', views.createpoint, name='createpoint'),
    path('deletematchtiebreak/<uuid:pk>', views.deletematchtiebreak, name='deletematchtiebreak'),
    path('changeserver/<uuid:pk>', views.changeserver, name='changeserver'),
    path('changeallservers/<uuid:pk>', views.changeallservers, name='changeallservers'),
    path('swappoints/<uuid:pk>', views.swappoints, name='swappoints'),
    path('invalid/<uuid:pk>', views.invalid, name='invalid'),
    path('viewstats/<uuid:pk>', views.viewstats, name="viewstats"),
]
