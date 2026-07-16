from django.shortcuts import render, redirect
from django.contrib import messages
from .models import User, UserProfile
import hashlib

# ── Helper function to hash password ──
# 🤔 Why? We never store plain passwords in database
# We convert "mypassword123" → "a8f5f167f44f..." (hashed)
# So even if database is hacked, passwords are safe!
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ── LANDING PAGE ──
def landing(request):
    # 🤔 Why? Just shows the landing HTML page to the user
    return render(request, 'DietMate_landing_updated.html')

# ── LOGIN PAGE ──
def login_view(request):
    # 🤔 Why request.method == 'POST'?
    # When user just visits the page = GET request (just show the page)
    # When user clicks Login button = POST request (process the form)
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        # Hash the password they typed
        hashed_password = hash_password(password)

        try:
            # 🤔 Why? Look for this email in our users table
            user = User.objects.get(email=email, password=hashed_password)

            
    
        #session for after signup, it automatically log the user in
            request.session['user_id'] = user.id
            request.session['user_name'] = user.full_name

            # Send them to dashboard
            return redirect('dashboard')

        except User.DoesNotExist:
            # 🤔 Why? If email or password is wrong, show error
            messages.error(request, 'Invalid email or password. Please try again.')
            return render(request, 'DietMate_login.html')

    # If just visiting the page (GET request) — just show the page
    return render(request, 'DietMate_login.html')

# ── SIGNUP PAGE ──
def signup(request):
    if request.method == 'POST':
        # 🤔 Why request.POST.get()?
        # This gets the data the user typed in the form fields
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        # 🤔 Why check passwords match?
        # To make sure user didn't make a typo in their password!
        if password != confirm_password:
            messages.error(request, 'Passwords do not match!')
            return render(request, 'DietMate_signup.html')

        # 🤔 Why check if email exists?
        # Each user must have a unique email — no duplicates allowed!
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered. Please login.')
            return render(request, 'DietMate_signup.html')

        # Hash the password before saving
        hashed_password = hash_password(password)

        # 🤔 Why User.objects.create()?
        # This saves the new user into our users table in MySQL!
        user = User.objects.create(
            full_name=full_name,
            email=email,
            password=hashed_password
        )

        # Save health info into user_profiles table
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

        # 🤔 Why UserProfile.objects.create()?
        # This saves health info into user_profiles table
        # linked to the user we just created above!
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
            food_preferences=food_preferences
        )

        # 🤔 Why session here too?
        # After signup, automatically log the user in!
        request.session['user_id'] = user.id
        request.session['user_name'] = user.full_name

        # Send them to dashboard
        return redirect('dashboard')

    return render(request, 'DietMate_signup.html')

# ── LOGOUT ──
def logout_view(request):
    # 🤔 Why flush()?
    # This deletes the session — user is now logged out
    # Like removing your theme park wristband!
    request.session.flush()
    return redirect('landing')

# ── DASHBOARD ──
def dashboard(request):
    # 🤔 Why check session?
    # If user is not logged in, send them to login page
    # We don't want strangers accessing the dashboard!
    if 'user_id' not in request.session:
        return redirect('login')

    user_id = request.session['user_id']
    user = User.objects.get(id=user_id)
    return render(request, 'DietMate_dashboard_v2.html', {'user': user})

# ── DIET PLAN ──
def diet_plan(request):
    if 'user_id' not in request.session:
        return redirect('login')
    return render(request, 'DietMate_dietplan.html')

# ── FITNESS PLAN ──
def fitness_plan(request):
    if 'user_id' not in request.session:
        return redirect('login')
    return render(request, 'DietMate_fitnessplan.html')

# ── PROGRESS ──
def progress(request):
    if 'user_id' not in request.session:
        return redirect('login')
    return render(request, 'DietMate_progress.html')

# ── CHATBOT ──
def chatbot(request):
    if 'user_id' not in request.session:
        return redirect('login')
    return render(request, 'DietMate_chatbot.html')

# ── DIETITIAN ──
def dietitian(request):
    if 'user_id' not in request.session:
        return redirect('login')
    return render(request, 'DietMate_dietitian.html')
