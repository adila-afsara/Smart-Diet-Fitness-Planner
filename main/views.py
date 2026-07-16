from django.shortcuts import render, redirect
from django.contrib import messages
from .models import User, UserProfile
import hashlib

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def landing(request):
    return render(request, 'DietMate_landing_updated.html')

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        hashed_password = hash_password(password)
        try:
            user = User.objects.get(email=email, password=hashed_password)
            request.session['user_id'] = user.id
            request.session['user_name'] = user.full_name
            return redirect('dashboard')
        except User.DoesNotExist:
            messages.error(request, 'Invalid email or password. Please try again.')
            return render(request, 'DietMate_login.html')
    return render(request, 'DietMate_login.html')

def signup(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if password != confirm_password:
            messages.error(request, 'Passwords do not match!')
            return render(request, 'DietMate_signup.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered. Please login.')
            return render(request, 'DietMate_signup.html')

        hashed_password = hash_password(password)
        user = User.objects.create(
            full_name=full_name,
            email=email,
            password=hashed_password
        )

        age = request.POST.get('age')
        weight = request.POST.get('weight')
        height = request.POST.get('height')
        gender = request.POST.get('gender')
        health_goal = request.POST.get('health_goal')
        health_condition = request.POST.get('health_condition')
        activity_level = request.POST.get('activity_level')
        workout_location = request.POST.get('workout_location')
        weekly_budget = request.POST.get('weekly_budget')
        food_preferences = request.POST.get('food_preferences')
        avoid_foods = request.POST.get('avoid_foods')

        UserProfile.objects.create(
            user=user,
            age=age,
            weight=weight,
            height=height,
            gender=gender,
            health_goal=health_goal,
            health_condition=health_condition,
            activity_level=activity_level,
            workout_location=workout_location,
            weekly_budget=weekly_budget,
            food_preferences=food_preferences,
            avoid_foods=avoid_foods
        )

        request.session['user_id'] = user.id
        request.session['user_name'] = user.full_name
        return redirect('dashboard')

    return render(request, 'DietMate_signup.html')

def logout_view(request):
    request.session.flush()
    return redirect('landing')

def dashboard(request):
    if 'user_id' not in request.session:
        return redirect('login')
    user_id = request.session['user_id']
    user = User.objects.get(id=user_id)
    return render(request, 'DietMate_dashboard_v2.html', {'user': user})

def diet_plan(request):
    if 'user_id' not in request.session:
        return redirect('login')
    return render(request, 'DietMate_dietplan.html')

def fitness_plan(request):
    if 'user_id' not in request.session:
        return redirect('login')
    return render(request, 'DietMate_fitnessplan.html')

def progress(request):
    if 'user_id' not in request.session:
        return redirect('login')
    return render(request, 'DietMate_progress.html')

def chatbot(request):
    if 'user_id' not in request.session:
        return redirect('login')
    return render(request, 'DietMate_chatbot.html')

def dietitian(request):
    if 'user_id' not in request.session:
        return redirect('login')
    return render(request, 'DietMate_dietitian.html')
