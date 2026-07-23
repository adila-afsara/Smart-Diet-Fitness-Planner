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

    user_id = request.session['user_id']
    user = User.objects.get(id=user_id)

    try:
        profile = UserProfile.objects.get(user=user)
    except UserProfile.DoesNotExist:
        return redirect('dashboard')

    from .models import DietPlan, DietPlanMeal
    from datetime import date, timedelta
    import json

    active_plan = DietPlan.objects.filter(
        user=user,
        plan_status='Active'
    ).first()

    if not active_plan:
        from .agents import nutrition_agent

        user_profile = {
            'age': profile.age,
            'weight': profile.weight,
            'height': profile.height,
            'gender': profile.gender,
            'health_goal': profile.health_goal,
            'health_condition': profile.health_condition,
            'weekly_budget': profile.weekly_budget,
            'food_preferences': profile.food_preferences,
            'avoid_foods': profile.avoid_foods,
        }

        # Call AI agent
        ai_response = nutrition_agent(user_profile)

        # 🤔 Why try/except here?
        # AI might return extra text around JSON sometimes
        # We try to clean and parse it safely!
        try:
            # Clean response — remove markdown if any
            clean = ai_response.strip()
            if clean.startswith('```'):
                clean = clean.split('```')[1]
                if clean.startswith('json'):
                    clean = clean[4:]
            clean = clean.strip()

            meal_data = json.loads(clean)

            # Save plan to database
            today = date.today()
            active_plan = DietPlan.objects.create(
                user=user,
                plan_start_date=today,
                plan_end_date=today + timedelta(days=15),
                plan_status='Active'
            )

            # Save each meal to database
            for day_data in meal_data:
                day_num = day_data.get('day')
                for meal in day_data.get('meals', []):
                    DietPlanMeal.objects.create(
                        plan=active_plan,
                        day_number=day_num,
                        meal_type=meal.get('meal_type'),
                        meal_name=meal.get('meal_name'),
                        ingredients=meal.get('ingredients'),
                        calories=meal.get('calories'),
                        protein=meal.get('protein'),
                        carbs=meal.get('carbs'),
                        fats=meal.get('fats'),
                        estimated_cost_bdt=meal.get('cost_bdt')
                    )

        except Exception as e:
            print(f"Error parsing AI response: {e}")
            print(f"AI Response was: {ai_response}")

    # Get today's day number in the plan
    from datetime import date
    if active_plan:
        today = date.today()
        day_number = (today - active_plan.plan_start_date).days + 1
        if day_number < 1:
            day_number = 1
        if day_number > 15:
            day_number = 15

        # Get today's meals from database
        todays_meals = DietPlanMeal.objects.filter(
            plan=active_plan,
            day_number=day_number
        )

        # Get all meals grouped by day
        all_meals = {}
        for d in range(1, 16):
            all_meals[d] = DietPlanMeal.objects.filter(
                plan=active_plan,
                day_number=d
            )

        # Calculate daily totals for today
        total_calories = sum(m.calories or 0 for m in todays_meals)
        total_cost = sum(m.estimated_cost_bdt or 0 for m in todays_meals)
        total_protein = sum(float(m.protein or 0) for m in todays_meals)
        total_carbs = sum(float(m.carbs or 0) for m in todays_meals)
        total_fats = sum(float(m.fats or 0) for m in todays_meals)

        return render(request, 'DietMate_dietplan.html', {
            'user': user,
            'profile': profile,
            'plan': active_plan,
            'todays_meals': todays_meals,
            'all_meals': all_meals,
            'day_number': day_number,
            'day_range': range(1, 16),
            'total_calories': total_calories,
            'total_calories': total_calories,
            'total_cost': total_cost,
            'total_protein': round(total_protein, 1),
            'total_carbs': round(total_carbs, 1),
            'total_fats': round(total_fats, 1),
            'daily_budget': round(float(profile.weekly_budget or 0) / 7, 2),

        })

    return render(request, 'DietMate_dietplan.html', {
        'user': user,
        'profile': profile,
        'plan': None,
    })



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
