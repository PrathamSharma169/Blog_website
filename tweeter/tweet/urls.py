from django.contrib import admin
from django.urls import path,include
from . import views
from django.conf import settings

urlpatterns = [
    # path('tweet/',include('tweet.urls'))
    path('',views.tweet_list,name='tweet_list'),
    path('create/',views.create_tweet,name='tweet_create'),
    path('<int:tweet_id>/edit/',views.edit_tweet,name='tweet_edit'),
    path('<int:tweet_id>/delete/',views.delete_tweet,name='tweet_delete'),
    path('register/',views.login,name='register'),
    # path("__reload__/", include("django_browser_reload.urls"))
]
