
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
    path('medical-specialist/', views.medical_specialist, name='medical_specialist'),
    path(
    "medical-specialist/<int:specialist_id>/",
    views.medical_specialist_detail,
    name="medical_specialist_detail"
    ),
    path('regenerate-plan/', views.regenerate_plan, name='regenerate_plan'),
    path('download-plan/', views.download_plan, name='download_plan'),
    path('toggle-exercise/<int:exercise_id>/', views.toggle_exercise_completion, name='toggle_exercise'),
    path(
    'fitness-plan/regenerate/',
    views.regenerate_fitness_plan,
    name='regenerate_fitness_plan'
    ),
    ] 
