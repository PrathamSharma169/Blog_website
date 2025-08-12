from django.contrib import admin
from django.urls import path,include
from . import views
from django.conf import settings
from django.contrib.auth import views as auth_views

urlpatterns = [
    # path('tweet/',include('tweet.urls'))
    path('',views.tweet_list,name='tweet_list'),
    path('create/',views.create_tweet,name='tweet_create'),
    path('<int:tweet_id>/edit/',views.edit_tweet,name='tweet_edit'),
    path('<int:tweet_id>/delete/',views.delete_tweet,name='tweet_delete'),
    path('<int:tweet_id>/user_tweet/',views.tweet,name='tweet'),
    path('register/',views.register,name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('mytweet/',views.my_tweets,name='my_tweets'),
    path('search/', views.search_tweets, name='tweet_search'),
    path('<int:tweet_id>/like/', views.toggle_like, name='toggle_like'),
    path('<int:tweet_id>/<int:comment_id>/delete_comment/', views.comment_delete, name='comment_delete'),
    path('<int:tweet_id>/comment/', views.comment_create, name='comment_get'),
    path('<int:tweet_id>/', views.tweet_detail, name='tweet_detail'),
    path('tweet/<int:tweet_id>/', views.tweet_detail, name='tweet_page'),
    path('<int:tweet_id>/analysis',views.comment_sentiment_list, name='comment_sentiment_list'),
    path('<int:tweet_id>/<str:sentiment>/count_analysis',views.sentiment_list, name='sentiment_list'),
    path('ai-helper/', views.ai_tweet_helper, name='ai_tweet_helper'),
    path('<int:user_id>/profile/', views.user_profile, name='user_profile'),
    # path("__reload__/", include("django_browser_reload.urls"))
]
