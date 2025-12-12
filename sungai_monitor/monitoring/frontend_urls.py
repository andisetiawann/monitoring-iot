from django.urls import path
from . import frontend_views

urlpatterns = [
    path('', frontend_views.dashboard, name='dashboard'),
    path('login/', frontend_views.login_view, name='login'),
    path('register/', frontend_views.register_view, name='register'),
    path('logout/', frontend_views.logout_view, name='logout'),
]
