from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('auth/register/', views.UserRegistrationView.as_view(), name='register'),
]