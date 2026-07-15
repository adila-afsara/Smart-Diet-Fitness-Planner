
from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing, name='landing'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('diet-plan/', views.diet_plan, name='diet_plan'),
    path('fitness-plan/', views.fitness_plan, name='fitness_plan'),
    path('progress/', views.progress, name='progress'),
    path('chatbot/', views.chatbot, name='chatbot'),
    path('dietitian/', views.dietitian, name='dietitian'),
]