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

        ai_response = nutrition_agent(user_profile)

        try:
            clean = ai_response.strip()
            if clean.startswith('```'):
                clean = clean.split('```')[1]
                if clean.startswith('json'):
                    clean = clean[4:]
            clean = clean.strip()

            meal_data = json.loads(clean)

            if len(meal_data) < 15:
                print(f"Incomplete plan generated — only {len(meal_data)} days. Not saving.")
                raise ValueError("Incomplete plan")

            today = date.today()
            active_plan = DietPlan.objects.create(
                user=user,
                plan_start_date=today,
                plan_end_date=today + timedelta(days=15),
                plan_status='Active'
            )

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

    from datetime import date
    if active_plan:
        today = date.today()
        day_number = (today - active_plan.plan_start_date).days + 1
        if day_number < 1:
            day_number = 1
        if day_number > 15:
            day_number = 15

        todays_meals = DietPlanMeal.objects.filter(
            plan=active_plan,
            day_number=day_number
        )

        all_meals = {}
        for d in range(1, 16):
            all_meals[d] = DietPlanMeal.objects.filter(
                plan=active_plan,
                day_number=d
            )

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


# List of rotating fitness tips — one is picked per day based on day_number
FITNESS_TIPS = [
    "Drink a glass of water before your workout and another after. Staying hydrated helps you perform better and recover faster! 💧",
    "Warm up for 5 minutes before starting — it reduces injury risk and improves performance. 🔥",
    "Focus on your form over speed, especially for strength exercises like squats and push-ups. 🧘",
    "Getting 7-8 hours of sleep helps your muscles recover and grow stronger overnight. 😴",
    "Eat a light snack with some protein about 30 minutes before your workout for extra energy. 🍌",
    "Consistency beats intensity — showing up daily matters more than one perfect workout. 📅",
    "Stretch after your workout, not just before — it helps reduce muscle soreness the next day. 🤸",
    "Listen to your body — if something hurts (not just feels tough), it's okay to rest that area. 🩺",
]

def fitness_plan(request):
    if 'user_id' not in request.session:
        return redirect('login')

    user_id = request.session['user_id']
    user = User.objects.get(id=user_id)

    try:
        profile = UserProfile.objects.get(user=user)
    except UserProfile.DoesNotExist:
        return redirect('dashboard')

    from .models import FitnessPlan, FitnessPlanExercise
    from datetime import date, timedelta
    import json

    active_plan = FitnessPlan.objects.filter(
        user=user,
        plan_status='Active'
    ).first()

    if not active_plan:
        from .agents import fitness_agent

        user_profile = {
            'age': profile.age,
            'weight': profile.weight,
            'health_goal': profile.health_goal,
            'activity_level': profile.activity_level,
            'workout_location': profile.workout_location,
            'health_condition': profile.health_condition,
        }

        ai_response = fitness_agent(user_profile)

        try:
            clean = ai_response.strip()
            if clean.startswith('```'):
                clean = clean.split('```')[1]
                if clean.startswith('json'):
                    clean = clean[4:]
            clean = clean.strip()

            plan_data = json.loads(clean)

            if len(plan_data) < 15:
                print(f"Incomplete fitness plan generated — only {len(plan_data)} days. Not saving.")
                raise ValueError("Incomplete fitness plan")

            today = date.today()
            active_plan = FitnessPlan.objects.create(
                user=user,
                plan_start_date=today,
                plan_end_date=today + timedelta(days=15),
                fitness_level=profile.activity_level,
                workout_location=profile.workout_location,
                plan_status='Active'
            )

            for day_data in plan_data:
                day_num = day_data.get('day')
                if day_data.get('is_rest_day'):
                    continue
                for ex in day_data.get('exercises', []):
                    FitnessPlanExercise.objects.create(
                        fitness_plan=active_plan,
                        day_number=day_num,
                        exercise_name=ex.get('exercise_name'),
                        duration_minutes=ex.get('duration_minutes'),
                        sets=ex.get('sets'),
                        reps=ex.get('reps'),
                        calories_burned=ex.get('calories_burned')
                    )

        except Exception as e:
            print(f"Error parsing AI fitness response: {e}")
            print(f"AI Response was: {ai_response}")

    if active_plan:
        today = date.today()
        day_number = (today - active_plan.plan_start_date).days + 1
        if day_number < 1:
            day_number = 1
        if day_number > 15:
            day_number = 15

        todays_exercises = FitnessPlanExercise.objects.filter(
            fitness_plan=active_plan,
            day_number=day_number
        )

        is_rest_day = not todays_exercises.exists()
        total_duration = sum(e.duration_minutes or 0 for e in todays_exercises)
        total_calories = sum(e.calories_burned or 0 for e in todays_exercises)

        daily_tip = FITNESS_TIPS[(day_number - 1) % len(FITNESS_TIPS)]

        return render(request, 'DietMate_fitnessplan.html', {
            'user': user,
            'profile': profile,
            'plan': active_plan,
            'todays_exercises': todays_exercises,
            'is_rest_day': is_rest_day,
            'day_number': day_number,
            'day_range': range(1, 16),
            'total_duration': total_duration,
            'total_calories': total_calories,
            'daily_tip': daily_tip,
        })

    return render(request, 'DietMate_fitnessplan.html', {
        'user': user,
        'profile': profile,
        'plan': None,
    })


def progress(request):
    if 'user_id' not in request.session:
        return redirect('login')

    user_id = request.session['user_id']
    user = User.objects.get(id=user_id)

    try:
        profile = UserProfile.objects.get(user=user)
    except UserProfile.DoesNotExist:
        return redirect('dashboard')

    from .models import DailyLog, BMIRecord
    from datetime import date
    from decimal import Decimal

    if request.method == 'POST':
        current_weight = request.POST.get('current_weight')
        water_glasses = request.POST.get('water_glasses')
        meal_followed = request.POST.get('meal_followed') == 'on'
        exercise_completed = request.POST.get('exercise_completed') == 'on'
        feeling = request.POST.get('feeling')

        if current_weight:
            current_weight = Decimal(current_weight)

            # Convert glasses to liters (1 glass ≈ 0.25L) for the DailyLog model
            water_liters = None
            if water_glasses:
                water_liters = Decimal(water_glasses) * Decimal('0.25')

            DailyLog.objects.create(
                user=user,
                log_date=date.today(),
                current_weight=current_weight,
                water_intake_liters=water_liters,
                meal_followed=meal_followed,
                exercise_completed=exercise_completed,
                notes=feeling
            )

            # Calculate and save BMI using the profile's height
            if profile.height:
                height_m = float(profile.height) / 100
                bmi_value = round(float(current_weight) / (height_m ** 2), 2)

                if bmi_value < 18.5:
                    bmi_category = 'Underweight'
                elif bmi_value < 25:
                    bmi_category = 'Normal Weight'
                elif bmi_value < 30:
                    bmi_category = 'Overweight'
                else:
                    bmi_category = 'Obese'

                BMIRecord.objects.create(
                    user=user,
                    weight=current_weight,
                    height=profile.height,
                    bmi_value=bmi_value,
                    bmi_category=bmi_category
                )

        return redirect('progress')

    # Get all logs and BMI records for this user, most recent first
    all_logs = DailyLog.objects.filter(user=user).order_by('-log_date')
    all_bmi_records = BMIRecord.objects.filter(user=user).order_by('-recorded_at')

    latest_log = all_logs.first()
    latest_bmi = all_bmi_records.first()
    first_log = all_logs.order_by('log_date').first()

    # Weight change since the very first logged entry
    weight_change = None
    if latest_log and first_log and latest_log != first_log:
        weight_change = float(latest_log.current_weight) - float(first_log.current_weight)

    # BMI change since the first recorded BMI
    bmi_change = None
    first_bmi = all_bmi_records.order_by('recorded_at').first()
    if latest_bmi and first_bmi and latest_bmi != first_bmi:
        bmi_change = float(latest_bmi.bmi_value) - float(first_bmi.bmi_value)

    # Exercise completion rate over logged days
    total_logs = all_logs.count()
    exercise_done_count = all_logs.filter(exercise_completed=True).count()
    meal_done_count = all_logs.filter(meal_followed=True).count()
    exercise_rate = round((exercise_done_count / total_logs) * 100) if total_logs else 0
    meal_rate = round((meal_done_count / total_logs) * 100) if total_logs else 0

    # Water intake today, in glasses (stored in liters, so convert back)
    water_today_glasses = None
    if latest_log and latest_log.water_intake_liters:
        water_today_glasses = round(float(latest_log.water_intake_liters) / 0.25)

    # Recent logs for the history table (most recent 8)
    recent_logs = list(all_logs[:8])
    recent_logs.reverse()  # show oldest to newest, left to right feel

    return render(request, 'DietMate_progress.html', {
        'user': user,
        'profile': profile,
        'latest_log': latest_log,
        'latest_bmi': latest_bmi,
        'weight_change': round(weight_change, 1) if weight_change is not None else None,
        'bmi_change': round(bmi_change, 1) if bmi_change is not None else None,
        'exercise_rate': exercise_rate,
        'meal_rate': meal_rate,
        'water_today_glasses': water_today_glasses,
        'recent_logs': recent_logs,
        'total_logs': total_logs,
         'today': date.today(),
    })
    

def chatbot(request):
    if 'user_id' not in request.session:
        return redirect('login')
    return render(request, 'DietMate_chatbot.html')

def dietitian(request):
    if 'user_id' not in request.session:
        return redirect('login')
    return render(request, 'DietMate_dietitian.html')
