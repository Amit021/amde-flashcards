# flashcards/urls.py

from django.urls import path
from allauth.account.views import LoginView, LogoutView
from . import views

urlpatterns = [
    path("", views.select_stack_view, name="select_stack"),
    path("flashcard/", views.flashcard_view, name="flashcard"),
    path('select_stack/', views.select_stack_view, name='select_stack'),
    path('reset_progress/', views.reset_progress, name='reset_progress'),
    path('accounts/login/', LoginView.as_view(), name='account_login'),
    path('accounts/logout/', LogoutView.as_view(), name='account_logout'),
]
