from django.urls import path
from .api import *


urlpatterns = [

    path('sign-in', SignInView.as_view(), name='sign-in'),
    path('sign-up', SignUpView.as_view(), name='sign-up'),
    path('sign-out', SignOutView.as_view(), name='sign-out'),
    path('profile', ProfileView.as_view(), name='profile'),
    path('profile/password', ChangePasswordAPIView.as_view()),
    path('profile/avatar', UpdateAvatarAPIView.as_view()),
]
