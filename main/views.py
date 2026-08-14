from django.shortcuts import render, redirect, get_object_or_404
from .models import DailyLog, BMIRecord, WeeklyReport, DietPlan
import traceback
from django.db.models import Q
from django.contrib import messages
from .models import User, UserProfile, DietPlan, MedicalSpecialist
from .agents import nutrition_agent, medical_specialist_agent, parse_gemini_json
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from .nutrition_calculator import (
    calculate_bmr,
    calculate_tdee,
    calculate_daily_calories,
)
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
        location = request.POST.get('location')
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
            location=location,
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

    print("Active Plan =", active_plan)
    plan_completed = False

    # Generate AI plan only if no active plan exists
    if not active_plan:

        user_profile = {
            'age': profile.age,
            'weight': profile.weight,
            'height': profile.height,
            'gender': profile.gender,
            'health_goal': profile.health_goal,
            'activity_level': profile.activity_level,
            'health_condition': profile.health_condition,
            'weekly_budget': profile.weekly_budget,
            'food_preferences': profile.food_preferences,
            'avoid_foods': profile.avoid_foods,
        }

        ai_response = nutrition_agent(user_profile)

        try:
            clean = ai_response.strip()

            if clean.startswith("```"):
                clean = clean.split("```")[1]
                if clean.startswith("json"):
                    clean = clean[4:]

            clean = clean.strip()

            meal_data = json.loads(clean)

            if len(meal_data) < 15:
                print(f"Incomplete plan generated — only {len(meal_data)} days.")
                raise ValueError("Incomplete plan")

            today = date.today()

            active_plan = DietPlan.objects.create(
                user=user,
                plan_start_date=today,
                plan_end_date=today + timedelta(days=14),
                plan_status='Active'
            )

            for day_data in meal_data:
                day_num = day_data.get("day")

                for meal in day_data.get("meals", []):

                    DietPlanMeal.objects.create(
                        plan=active_plan,
                        day_number=day_num,
                        meal_type=meal.get("meal_type"),
                        meal_name=meal.get("meal_name"),
                        ingredients=meal.get("ingredients"),
                        calories=meal.get("calories"),
                        protein=meal.get("protein"),
                        carbs=meal.get("carbs"),
                        fats=meal.get("fats"),
                        estimated_cost_bdt=meal.get("cost_bdt")
                    )

        except Exception as e:
            print("Error parsing AI response:", e)
            print(ai_response)

    # If a plan exists, show it
    if active_plan:

        today = date.today()

        day_number = (today - active_plan.plan_start_date).days + 1

        if day_number < 1:
            day_number = 1

        if day_number > 15:
            active_plan.plan_status = "Completed"
            active_plan.save()
            plan_completed = True
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
        total_cost = float(sum(m.estimated_cost_bdt or 0 for m in todays_meals))
        total_protein = sum(float(m.protein or 0) for m in todays_meals)
        total_carbs = sum(float(m.carbs or 0) for m in todays_meals)
        total_fats = sum(float(m.fats or 0) for m in todays_meals)

        # Calculate calorie target
        bmr = calculate_bmr(
            float(profile.weight),
            float(profile.height),
            int(profile.age),
            profile.gender
        )

        tdee = calculate_tdee(
            bmr,
            profile.activity_level
        )

        daily_calorie_target = calculate_daily_calories(
            tdee,
            profile.health_goal
        )
        daily_budget = round(float(profile.weekly_budget or 0) / 7, 2)
        remaining_budget = daily_budget - total_cost

        if remaining_budget < 0:
          remaining_budget = 0
        return render(request, 'DietMate_dietplan.html', {
            'user': user,
            'profile': profile,
            'plan': active_plan,
            'todays_meals': todays_meals,
            'all_meals': all_meals,
            'day_number': day_number,
            'plan_completed': plan_completed,
            'day_range': range(1, 16),
            'total_calories': total_calories,
            'total_cost': total_cost,
            'total_protein': round(total_protein, 1),
            'total_carbs': round(total_carbs, 1),
            'total_fats': round(total_fats, 1),
            'daily_budget':  daily_budget,
            'remaining_budget': round(remaining_budget, 2),
            'daily_calorie_target': daily_calorie_target,
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

    # =========================================================
    # FIND ACTIVE FITNESS PLAN
    # =========================================================

    active_plan = FitnessPlan.objects.filter(
        user=user,
        plan_status='Active'
    ).first()

    # =========================================================
    # GENERATE NEW PLAN IF NO ACTIVE PLAN EXISTS
    # =========================================================

    if not active_plan:

        from .fitness_strategies import get_fitness_strategy

        user_profile = {
            'age': profile.age,
            'weight': profile.weight,
            'health_goal': profile.health_goal,
            'activity_level': profile.activity_level,
            'workout_location': profile.workout_location,
            'health_condition': profile.health_condition,
        }

        # Strategy Pattern
        strategy = get_fitness_strategy(
            profile.activity_level
        )

        ai_response = strategy.generate_plan(
            user_profile
        )

        try:
            clean = ai_response.strip()

            # Remove Markdown code block if Gemini returns one
            if clean.startswith('```'):
                clean = clean.split('```')[1]

                if clean.startswith('json'):
                    clean = clean[4:]

            clean = clean.strip()

            plan_data = json.loads(clean)

            # Make sure all 15 days were generated
            if len(plan_data) < 15:

                print(
                    f"Incomplete fitness plan generated — "
                    f"only {len(plan_data)} days. Not saving."
                )

                raise ValueError(
                    "Incomplete fitness plan"
                )

            # Create 15-day plan
            today = date.today()

            active_plan = FitnessPlan.objects.create(
                user=user,
                plan_start_date=today,
                plan_end_date=today + timedelta(days=14),
                fitness_level=profile.activity_level,
                workout_location=profile.workout_location,
                plan_status='Active'
            )

            # Save exercises
            for day_data in plan_data:

                day_num = day_data.get('day')

                # Skip rest days
                if day_data.get('is_rest_day'):
                    continue

                for ex in day_data.get(
                    'exercises',
                    []
                ):

                    FitnessPlanExercise.objects.create(
                        fitness_plan=active_plan,
                        day_number=day_num,
                        exercise_name=ex.get(
                            'exercise_name'
                        ),
                        duration_minutes=ex.get(
                            'duration_minutes'
                        ),
                        sets=ex.get('sets'),
                        reps=ex.get('reps'),
                        calories_burned=ex.get(
                            'calories_burned'
                        )
                    )

        except Exception as e:

            print(
                f"Error parsing AI fitness response: {e}"
            )

            print(
                f"AI Response was: {ai_response}"
            )

    # =========================================================
    # DISPLAY ACTIVE PLAN
    # =========================================================

    if active_plan:

        today = date.today()

        # Calculate current day
        day_number = (
            today - active_plan.plan_start_date
        ).days + 1

        if day_number < 1:
            day_number = 1

        if day_number > 15:
            day_number = 15

        # =====================================================
        # TODAY'S EXERCISES
        # =====================================================

        todays_exercises = FitnessPlanExercise.objects.filter(
            fitness_plan=active_plan,
            day_number=day_number
        )

        # =====================================================
        # ALL EXERCISES
        # =====================================================

        all_exercises = FitnessPlanExercise.objects.filter(
            fitness_plan=active_plan
        ).order_by(
            'day_number',
            'id'
        )

        # =====================================================
        # TODAY'S COMPLETED EXERCISES
        # =====================================================

        completed_exercises = todays_exercises.filter(
            is_completed=True
        ).count()

        # =====================================================
        # TODAY'S TOTAL DURATION
        # =====================================================

        total_duration = sum(
            exercise.duration_minutes or 0
            for exercise in todays_exercises
        )

        # =====================================================
        # TODAY'S TOTAL CALORIES
        # =====================================================

        total_calories = sum(
            exercise.calories_burned or 0
            for exercise in todays_exercises
        )

        # =====================================================
        # TOTAL PLAN CALORIES
        # =====================================================

        total_plan_calories = sum(
            exercise.calories_burned or 0
            for exercise in all_exercises
        )

        # =====================================================
        # TOTAL PLAN DURATION
        # =====================================================

        total_plan_duration = sum(
            exercise.duration_minutes or 0
            for exercise in all_exercises
        )

        # =====================================================
        # WEEK 1 EXERCISES
        # =====================================================

        week1_exercises = all_exercises.filter(
            day_number__range=(1, 7)
        )

        # =====================================================
        # WEEK 1 COMPLETED DAYS
        # =====================================================

        completed_days = 0

        for day in range(1, 8):

            day_exercises = all_exercises.filter(
                day_number=day
            )

            # Rest day
            if not day_exercises.exists():

                completed_days += 1

            # Workout day
            elif not day_exercises.filter(
                is_completed=False
            ).exists():

                completed_days += 1

        week1_percentage = round(
            (completed_days / 7) * 100
        )

        # =====================================================
        # EXERCISE CATEGORIES
        # =====================================================

        cardio_keywords = [
            'walk',
            'jog',
            'run',
            'treadmill',
            'cycling',
            'bike',
            'rowing',
            'stair',
            'hiit',
            'jump',
            'cardio'
        ]

        strength_keywords = [
            'squat',
            'press',
            'pull',
            'push',
            'curl',
            'row',
            'lunge',
            'deadlift',
            'barbell',
            'dumbbell',
            'plank',
            'strength'
        ]

        stretching_keywords = [
            'stretch',
            'yoga',
            'mobility',
            'flexibility'
        ]

        # =====================================================
        # CATEGORY FUNCTION
        # =====================================================

        def get_category(exercise_name):

            name = (
                exercise_name or ''
            ).lower()

            if any(
                keyword in name
                for keyword in cardio_keywords
            ):
                return 'cardio'

            if any(
                keyword in name
                for keyword in stretching_keywords
            ):
                return 'stretching'

            if any(
                keyword in name
                for keyword in strength_keywords
            ):
                return 'strength'

            return 'strength'

        # =====================================================
        # CATEGORY COUNTERS
        # =====================================================

        cardio_total = 0
        cardio_completed = 0

        strength_total = 0
        strength_completed = 0

        stretching_total = 0
        stretching_completed = 0

        for exercise in week1_exercises:

            category = get_category(
                exercise.exercise_name
            )

            if category == 'cardio':

                cardio_total += 1

                if exercise.is_completed:
                    cardio_completed += 1

            elif category == 'strength':

                strength_total += 1

                if exercise.is_completed:
                    strength_completed += 1

            elif category == 'stretching':

                stretching_total += 1

                if exercise.is_completed:
                    stretching_completed += 1

        # =====================================================
        # CATEGORY PERCENTAGES
        # =====================================================

        cardio_percentage = (
            round(
                (cardio_completed / cardio_total) * 100
            )
            if cardio_total
            else 0
        )

        strength_percentage = (
            round(
                (strength_completed / strength_total) * 100
            )
            if strength_total
            else 0
        )

        stretching_percentage = (
            round(
                (stretching_completed / stretching_total) * 100
            )
            if stretching_total
            else 0
        )

        # =====================================================
        # CREATE ALL 15 DAYS
        # =====================================================

        plan_days = []

        for day in range(1, 16):

            exercises = all_exercises.filter(
                day_number=day
            )

            plan_days.append({
                'day_number': day,
                'exercises': exercises,
                'is_rest_day': not exercises.exists(),
            })

        # =====================================================
        # TODAY REST DAY?
        # =====================================================

        is_rest_day = not todays_exercises.exists()

        # =====================================================
        # DAILY TIP
        # =====================================================

        daily_tip = FITNESS_TIPS[
            (day_number - 1)
            % len(FITNESS_TIPS)
        ]

        # =====================================================
        # SEND EVERYTHING TO TEMPLATE
        # =====================================================

        return render(
            request,
            'DietMate_fitnessplan.html',
            {
                'user': user,
                'profile': profile,
                'plan': active_plan,

                # Exercises
                'todays_exercises': todays_exercises,
                'all_exercises': all_exercises,
                'plan_days': plan_days,

                # Current day
                'is_rest_day': is_rest_day,
                'day_number': day_number,
                'day_range': range(1, 16),

                # Today's statistics
                'total_duration': total_duration,
                'total_calories': total_calories,

                # Whole plan statistics
                'total_plan_calories': total_plan_calories,
                'total_plan_duration': total_plan_duration,

                # Tips
                'daily_tip': daily_tip,

                # Completion
                'completed_exercises': completed_exercises,

                # Week 1
                'completed_days': completed_days,
                'week1_percentage': week1_percentage,

                # Categories
                'cardio_percentage': cardio_percentage,
                'strength_percentage': strength_percentage,
                'stretching_percentage': stretching_percentage,
            }
        )

    # =========================================================
    # NO PLAN
    # =========================================================

    return render(
        request,
        'DietMate_fitnessplan.html',
        {
            'user': user,
            'profile': profile,
            'plan': None,
        }
    )


# =============================================================
# TOGGLE EXERCISE COMPLETION
# =============================================================

def toggle_exercise_completion(
    request,
    exercise_id
):

    if 'user_id' not in request.session:
        return redirect('login')

    from .models import FitnessPlanExercise

    exercise = get_object_or_404(
        FitnessPlanExercise,
        id=exercise_id,
        fitness_plan__user_id=request.session['user_id']
    )

    # Toggle completion
    exercise.is_completed = (
        not exercise.is_completed
    )

    exercise.save()

    return redirect('fitness_plan')

def regenerate_fitness_plan(request):
    if request.method != "POST":
        return redirect("fitness_plan")

    if 'user_id' not in request.session:
        return redirect('login')

    user = User.objects.get(id=request.session['user_id'])

    from .models import FitnessPlan

    active_plan = FitnessPlan.objects.filter(
        user=user,
        plan_status='Active'
    ).first()

    # Mark the current plan as completed.
    # We DO NOT delete it because we want to keep it
    # as previous cycle history.
    if active_plan:
        active_plan.plan_status = "Completed"
        active_plan.save()

    # Redirect to fitness_plan.
    # Since there is now no Active plan, fitness_plan()
    # will automatically generate a new 15-day plan.
    return redirect("fitness_plan")
def progress(request):
    if 'user_id' not in request.session:
        return redirect('login')
    from .models import DailyLog, BMIRecord, DietPlan
    from datetime import date, timedelta
    from decimal import Decimal 

    user_id = request.session['user_id']
    user = User.objects.get(id=user_id)

    try:
        profile = UserProfile.objects.get(user=user)
    except UserProfile.DoesNotExist:
        return redirect('dashboard')

    from datetime import date

    today = date.today()

    # Find the user's active 15-day diet plan
    from .models import DietPlan

    active_plan = DietPlan.objects.filter(
        user=user,
        plan_status='Active'
    ).first()

    cycle_day = None

    if active_plan:
        cycle_day = (today - active_plan.plan_start_date).days + 1
        print("CYCLE DAY =", cycle_day)
    if cycle_day == 7:
       print("DAY 7 REACHED — WEEKLY REPORT SHOULD BE GENERATED")   
    if cycle_day == 2:
    # Get the first 7 days of this cycle
       week_logs = DailyLog.objects.filter(
           user=user,
           log_date__gte=active_plan.plan_start_date,
           log_date__lte=active_plan.plan_start_date + timedelta(days=6)
        ).order_by('log_date') 

    print("WEEKLY LOG COUNT =", week_logs.count())  
    starting_weight = week_logs.first().current_weight if week_logs.exists() else None
    ending_weight = week_logs.last().current_weight if week_logs.exists() else None

    weight_change = None

    if starting_weight is not None and ending_weight is not None:
       weight_change = ending_weight - starting_weight

    print("STARTING WEIGHT =", starting_weight)
    print("ENDING WEIGHT =", ending_weight)
    print("WEIGHT CHANGE =", weight_change)  


    if request.method == 'POST':
        current_weight = request.POST.get('current_weight')
        water_glasses = request.POST.get('water_glasses')
        calories_consumed = request.POST.get('calories_consumed')
        meal_followed = request.POST.get('meal_followed') == 'on'
        exercise_completed = request.POST.get('exercise_completed') == 'on'
        feeling = request.POST.get('feeling')

        if current_weight:
            current_weight = Decimal(current_weight)

            # Convert glasses to liters (1 glass ≈ 0.25L) for the DailyLog model
            water_liters = None
            if water_glasses:
                water_liters = Decimal(water_glasses) * Decimal('0.25')

            # update_or_create: if today's entry already exists, update it instead of
            # making a duplicate row for the same date
            DailyLog.objects.update_or_create(
                user=user,
                log_date=date.today(),
                defaults={
                    'current_weight': current_weight,
                    'water_intake_liters': water_liters,
                    'calories_consumed': int(calories_consumed) if calories_consumed else None,
                    'meal_followed': meal_followed,
                    'exercise_completed': exercise_completed,
                    'notes': feeling,
                }
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
                # Remove any earlier BMI record from today before adding the new one,
                # so re-saving today's log doesn't pile up duplicate BMI entries
                BMIRecord.objects.filter(user=user, recorded_at__date=date.today()).delete()
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
    # Look only at the last 7 days for the Weekly Progress percentages
    from datetime import timedelta
    week_start = date.today() - timedelta(days=6)  # today + 6 previous days = 7 total
    week_logs = all_logs.filter(log_date__gte=week_start)

    total_logs = all_logs.count()          # all-time count, still used for the stats row
    week_log_count = week_logs.count()     # this week's count, used for the % bars

    exercise_done_count = week_logs.filter(exercise_completed=True).count()
    meal_done_count = week_logs.filter(meal_followed=True).count()
    exercise_rate = round((exercise_done_count / week_log_count) * 100) if week_log_count else 0
    meal_rate = round((meal_done_count / week_log_count) * 100) if week_log_count else 0
    
    # Water intake today, in glasses (stored in liters, so convert back)
    water_today_glasses = None
    if latest_log and latest_log.water_intake_liters:
        water_today_glasses = round(float(latest_log.water_intake_liters) / 0.25)

    # Water goal rate — days this week where at least 2L (8 glasses) was logged
    water_goal_days = week_logs.filter(water_intake_liters__gte=2.0).count()
    water_goal_rate = round((water_goal_days / week_log_count) * 100) if week_log_count else 0

    # ── DAY 7 PROGRESS REPORT ──
    # Check whether the user is currently on Day 7 of their 15-day plan
    active_plan = DietPlan.objects.filter(
        user=user,
        plan_status='Active'
    ).first()

    if active_plan:
        current_day = (date.today() - active_plan.plan_start_date).days + 1

        if current_day == 7:

            # Get Day 1–7 logs
            cycle_logs = DailyLog.objects.filter(
                user=user,
                log_date__gte=active_plan.plan_start_date,
                log_date__lte=active_plan.plan_start_date + timedelta(days=6)
            ).order_by('log_date')

            # Get BMI records from Day 1–7
            cycle_bmis = BMIRecord.objects.filter(
                user=user,
                recorded_at__date__gte=active_plan.plan_start_date,
                recorded_at__date__lte=active_plan.plan_start_date + timedelta(days=6)
            ).order_by('recorded_at')

            if cycle_logs.exists():

                first_cycle_log = cycle_logs.first()
                last_cycle_log = cycle_logs.last()

                starting_weight = first_cycle_log.current_weight
                ending_weight = last_cycle_log.current_weight

                weight_change = (
                    ending_weight - starting_weight
                    if starting_weight is not None and ending_weight is not None
                    else None
                )

                starting_bmi = cycle_bmis.first().bmi_value if cycle_bmis.exists() else None
                ending_bmi = cycle_bmis.last().bmi_value if cycle_bmis.exists() else None

                # Prepare data for Health Tracking Agent
                user_data = {
                    'starting_weight': starting_weight,
                    'current_weight': ending_weight,
                    'height': profile.height,
                    'health_goal': profile.health_goal,
                    'health_condition': profile.health_condition,
                }

                agent_logs = {
                    'meal_follow_days': cycle_logs.filter(
                        meal_followed=True
                    ).count(),

                    'exercise_days': cycle_logs.filter(
                        exercise_completed=True
                    ).count(),

                    'avg_water': round(
                        sum(
                            float(log.water_intake_liters or 0)
                            for log in cycle_logs
                        ) / 7,
                        2
                    ),

                    'weight_change': round(
                        float(weight_change),
                        2
                    ) if weight_change is not None else 0,
                }

                # Generate AI progress report
                ai_report = health_tracking_agent(
                    user_data,
                    agent_logs
                )

                # Save report in database
                WeeklyReport.objects.update_or_create(
                    user=user,
                    week_start_date=active_plan.plan_start_date,
                    week_end_date=active_plan.plan_start_date + timedelta(days=6),
                    defaults={
                        'starting_weight': starting_weight,
                        'ending_weight': ending_weight,
                        'weight_change': weight_change,
                        'starting_bmi': starting_bmi,
                        'ending_bmi': ending_bmi,
                        'meal_follow_rate': round(
                            (cycle_logs.filter(
                                meal_followed=True
                            ).count() / 7) * 100
                        ),
                        'exercise_completion_rate': round(
                            (cycle_logs.filter(
                                exercise_completed=True
                            ).count() / 7) * 100
                        ),
                        'ai_feedback': ai_report,
                    }
                )

                print("Day 7 progress report generated successfully.")

    # Calories logged rate — days this week where calories_consumed was actually filled in
    calories_logged_days = week_logs.exclude(calories_consumed__isnull=True).count()
    calories_logged_rate = round((calories_logged_days / week_log_count) * 100) if week_log_count else 0

    # Simple rule-based feedback message based on the weakest area
    rates = {'meal plan': meal_rate, 'exercise': exercise_rate, 'water intake': water_goal_rate}
    weakest_area = min(rates, key=rates.get)
    if total_logs == 0:
        ai_feedback = "Log your first day to start getting personalized feedback here!"
    elif rates[weakest_area] >= 80:
        ai_feedback = f"Excellent consistency across the board! Keep up the great work, especially with your {weakest_area}."
    else:
        ai_feedback = f"You're doing well overall — try focusing a bit more on your {weakest_area}, it's at {rates[weakest_area]}% right now. Small improvements add up!"

    # Recent logs for the history table (most recent 8)
    recent_logs = list(all_logs[:8])
    recent_logs.reverse()  # show oldest to newest, left to right feel

    # Attach each log's matching same-day BMI value, since BMI lives in a separate table
    for log in recent_logs:
        matching_bmi = BMIRecord.objects.filter(user=user, recorded_at__date=log.log_date).first()
        log.bmi_display = matching_bmi.bmi_value if matching_bmi else None

    # Build Weight Trend chart data — last up to 8 logs, oldest to newest
    chart_logs = list(all_logs.order_by('log_date'))
    if len(chart_logs) > 8:
        chart_logs = chart_logs[-8:]

    weight_chart_points = []
    weight_polyline = ""
    weight_area_path = ""
    weight_y_labels = []
    chart_start_weight = None
    chart_current_weight = None
    chart_weight_change = None
    chart_weight_change_abs = None

    if chart_logs:
        weights = [float(l.current_weight) for l in chart_logs]
        min_w = min(weights)
        max_w = max(weights)
        if max_w == min_w:
            max_w = min_w + 1  # avoid a divide-by-zero on a perfectly flat line

        chart_left, chart_right = 60, 380
        chart_top, chart_bottom = 30, 155
        n = len(chart_logs)

        for i, log in enumerate(chart_logs):
            w = float(log.current_weight)
            x = chart_left if n == 1 else chart_left + (chart_right - chart_left) * (i / (n - 1))
            y = chart_bottom - ((w - min_w) / (max_w - min_w)) * (chart_bottom - chart_top)
            weight_chart_points.append({
                'x': round(x, 1),
                'y': round(y, 1),
                'weight': w,
                'date': log.log_date,
                'is_last': (i == n - 1),
            })

        weight_polyline = " ".join(f"{p['x']},{p['y']}" for p in weight_chart_points)

        first_p, last_p = weight_chart_points[0], weight_chart_points[-1]
        path_parts = [f"M{first_p['x']},{chart_bottom}"]
        path_parts += [f"L{p['x']},{p['y']}" for p in weight_chart_points]
        path_parts += [f"L{last_p['x']},{chart_bottom}", "Z"]
        weight_area_path = " ".join(path_parts)

        weight_y_labels = [
            round(max_w, 1),
            round(max_w - (max_w - min_w) / 3, 1),
            round(max_w - 2 * (max_w - min_w) / 3, 1),
            round(min_w, 1),
        ]

        chart_start_weight = weights[0]
        chart_current_weight = weights[-1]
        chart_weight_change = round(chart_current_weight - chart_start_weight, 1)
        chart_weight_change_abs = abs(chart_weight_change)

    return render(request, 'DietMate_progress.html', {
        'user': user,
        'profile': profile,
        'latest_log': latest_log,
        'latest_bmi': latest_bmi,
        'first_bmi': first_bmi,
        'all_bmi_records': all_bmi_records,
        'weight_change': round(weight_change, 1) if weight_change is not None else None,
        'weight_change_abs': round(abs(weight_change), 1) if weight_change is not None else None,
        'bmi_change': round(bmi_change, 1) if bmi_change is not None else None,
        'bmi_change_abs': round(abs(bmi_change), 1) if bmi_change is not None else None,
        'exercise_rate': exercise_rate,
        'meal_rate': meal_rate,
        'water_today_glasses': water_today_glasses,
        'recent_logs': recent_logs,
        'weight_chart_points': weight_chart_points,
        'weight_polyline': weight_polyline,
        'weight_area_path': weight_area_path,
        'weight_y_labels': weight_y_labels,
        'chart_start_weight': chart_start_weight,
        'chart_current_weight': chart_current_weight,
        'chart_weight_change': chart_weight_change,
        'chart_weight_change_abs': chart_weight_change_abs,
        'total_logs': total_logs,
        'today': date.today(),
        'water_goal_rate': water_goal_rate,
        'calories_logged_rate': calories_logged_rate,
        'ai_feedback': ai_feedback,
        'week_log_count': week_log_count,
    })
def chatbot(request):
    if 'user_id' not in request.session:
        return redirect('login')
    return render(request, 'DietMate_chatbot.html')
def medical_specialist(request):
    if 'user_id' not in request.session:
        return redirect('login')

    user_id = request.session['user_id']
    user = User.objects.get(id=user_id)

    try:
        profile = UserProfile.objects.get(user=user)
    except UserProfile.DoesNotExist:
        return redirect('dashboard')

    # Get search and filter parameters from GET request
    search_query = request.GET.get('search', '').strip()
    search_location = request.GET.get('location', '').strip()
    search_specialty = request.GET.get('specialty', '').strip()
    type_filter = request.GET.get('type', '').strip()

    # Build user profile for AI
    user_profile = {
        "age": profile.age,
        "gender": profile.gender,
        "height": profile.height,
        "weight": profile.weight,
        "health_goal": profile.health_goal,
        "health_condition": profile.health_condition,
        "activity_level": profile.activity_level,
        "food_preferences": profile.food_preferences,
        "avoid_foods": profile.avoid_foods,
        "location": search_location or profile.location or "",
        "search_query": search_query,
        "specialty_query": search_specialty,
    }

    # Set a default summary so the yellow banner is NEVER empty
    summary = "Recommended specialists tailored to your health profile and query."
    error_message = None

    # Check if we already have saved specialists for this user
    existing_specialists_count = MedicalSpecialist.objects.filter(user=user).count()

    # Call Gemini AI ONLY if user clicked search OR if no records exist yet
    should_fetch_ai = bool(search_query or search_location or search_specialty or existing_specialists_count == 0)

    if should_fetch_ai:
        try:
            # Call Gemini AI
            ai_response = medical_specialist_agent(user_profile)

            print("\n========== GEMINI RESPONSE ==========")
            print(ai_response)
            print("=====================================\n")

            data = parse_gemini_json(ai_response)

            if data is None:
                error_message = "Unable to fetch AI recommendations."
            else:
                # Use AI summary if present, otherwise fallback
                summary = data.get("summary") or "AI-recommended specialists tailored to your health profile."
                print("SUMMARY FROM GEMINI:", summary)
                recommended_specialists = data.get("recommended_specialists", [])


                print("Number of specialists received:", len(recommended_specialists))

                # Remove previous AI recommendations for this user
                MedicalSpecialist.objects.filter(user=user).delete()

                # Save new recommendations
                for specialist in recommended_specialists:
                    print("Saving:", specialist.get("full_name"))

                    MedicalSpecialist.objects.create(
                        user=user,
                        full_name=specialist.get("full_name"),
                        title=specialist.get("title"),
                        specialist_type=specialist.get("specialist_type"),
                        specialty=specialist.get("specialty"),
                        hospital_clinic=specialist.get("hospital_clinic"),
                        location=specialist.get("location"),
                        consultation_fee_bdt=specialist.get("consultation_fee_bdt"),
                        website=specialist.get("website"),
                        contact_number=specialist.get("contact_number"),
                        email=specialist.get("email"),
                        available_days=specialist.get("available_days"),
                        rating=specialist.get("rating"),
                        notes=specialist.get("notes"),
                        source=specialist.get("source", "Gemini AI")
                    )

                print("================================")
                print("Saved specialists:", MedicalSpecialist.objects.filter(user=user).count())
                print("================================")

        except Exception:
            error_message = "Unable to fetch AI recommendations."
            print("\n========== ERROR ==========")
            traceback.print_exc()
            print("===========================\n")

    # Fetch database specialists for the logged-in user
    specialists = MedicalSpecialist.objects.filter(user_id=user_id)

    # Apply database-level filters based on user selection
    if search_query:
        specialists = specialists.filter(
            Q(full_name__icontains=search_query) |
            Q(specialty__icontains=search_query) |
            Q(hospital_clinic__icontains=search_query) |
            Q(notes__icontains=search_query)
        )

    if search_location:
        specialists = specialists.filter(location__icontains=search_location)

    if search_specialty:
        specialists = specialists.filter(specialty__icontains=search_specialty)

    if type_filter:
        specialists = specialists.filter(specialist_type__iexact=type_filter)

    return render(
        request,
        "DietMate_medical_specialist.html",
        {
            "specialists": specialists,
            "summary": summary,
            "error_message": error_message,
            "user": user,
            "profile": profile,
        }
    )
def medical_specialist_detail(request, specialist_id):
    if 'user_id' not in request.session:
        return redirect('login')

    user = User.objects.get(id=request.session['user_id'])

    specialist = get_object_or_404(
        MedicalSpecialist,
        id=specialist_id,
        user=user
    )

    return render(
        request,
        "medical_specialist_detail.html",
        {
            "specialist": specialist
        }
    )
def regenerate_plan(request):
    if request.method != "POST":
        return redirect("diet_plan")

    if 'user_id' not in request.session:
        return redirect('login')

    user = User.objects.get(id=request.session['user_id'])

    from .models import DietPlan, DietPlanMeal

    active_plan = DietPlan.objects.filter(
        user=user,
        plan_status='Active'
    ).first()

    plan_completed = False

    
    if active_plan:
       active_plan.plan_status = "Completed"
       active_plan.save()

    return redirect('diet_plan')

def download_plan(request):
    if 'user_id' not in request.session:
        return redirect('login')

    user = User.objects.get(id=request.session['user_id'])
    profile = UserProfile.objects.get(user=user)

    from .models import DietPlan, DietPlanMeal

    active_plan = DietPlan.objects.filter(
        user=user,
        plan_status='Active'
    ).first()

    if not active_plan:
        return HttpResponse("No active diet plan found.")

    # Calculate calorie target
    bmr = calculate_bmr(
        float(profile.weight),
        float(profile.height),
        int(profile.age),
        profile.gender
    )

    tdee = calculate_tdee(
        bmr,
        profile.activity_level
    )

    daily_calorie_target = calculate_daily_calories(
        tdee,
        profile.health_goal
    )

    # Create PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="DietMate_DietPlan.pdf"'

    p = canvas.Canvas(response)

    # =============================
    # Title
    # =============================
    p.setFont("Helvetica-Bold", 18)
    p.drawString(180, 810, "DietMate")

    p.setFont("Helvetica", 13)
    p.drawString(130, 790, "Personalized 15-Day Diet Plan")

    # =============================
    # User Information
    # =============================
    y = 760

    p.setFont("Helvetica-Bold", 12)
    p.drawString(40, y, "User Information")

    y -= 20
    p.setFont("Helvetica", 11)
    p.drawString(40, y, f"Name: {user.full_name}")

    y -= 18
    p.drawString(40, y, f"Health Goal: {profile.health_goal}")

    y -= 18
    p.drawString(40, y, f"Weekly Budget: BDT {profile.weekly_budget}")

    y -= 18
    p.drawString(40, y, f"Daily Calorie Target: {daily_calorie_target} kcal")

    y -= 30

    # =============================
    # Meal Plan
    # =============================
    for day in range(1, 16):

        meals = DietPlanMeal.objects.filter(
            plan=active_plan,
            day_number=day
        )

        # Start a new page if needed
        if y < 120:
            p.showPage()
            y = 800

        p.setFont("Helvetica-Bold", 13)
        p.drawString(40, y, f"Day {day}")

        y -= 20

        p.setFont("Helvetica", 11)

        for meal in meals:

            p.drawString(
                50,
                y,
                f"{meal.meal_type}: {meal.meal_name}"
            )

            y -= 15

            p.drawString(
                70,
                y,
                f"Calories: {meal.calories} kcal   "
                f"Protein: {meal.protein} g   "
                f"Cost: BDT {meal.estimated_cost_bdt}"
            )

            y -= 20

        y -= 10 

    p.save()

    return response

def download_fitness_plan(request):
    if 'user_id' not in request.session:
        return redirect('login')

    user = User.objects.get(id=request.session['user_id'])
    profile = UserProfile.objects.get(user=user)

    from .models import FitnessPlan, FitnessPlanExercise

    active_plan = FitnessPlan.objects.filter(
        user=user,
        plan_status='Active'
    ).first()

    if not active_plan:
        return HttpResponse("No active fitness plan found.")

    # =============================
    # Create PDF
    # =============================

    response = HttpResponse(
        content_type='application/pdf'
    )

    response['Content-Disposition'] = (
        'attachment; filename="DietMate_FitnessPlan.pdf"'
    )

    p = canvas.Canvas(response)

    # =============================
    # Title
    # =============================

    p.setFont("Helvetica-Bold", 18)
    p.drawString(180, 810, "DietMate")

    p.setFont("Helvetica", 13)
    p.drawString(130, 790, "Personalized 15-Day Fitness Plan")

    # =============================
    # User Information
    # =============================

    y = 760

    p.setFont("Helvetica-Bold", 12)
    p.drawString(40, y, "User Information")

    y -= 20

    p.setFont("Helvetica", 11)
    p.drawString(
        40,
        y,
        f"Name: {user.full_name}"
    )

    y -= 18

    p.drawString(
        40,
        y,
        f"Health Goal: {profile.health_goal}"
    )

    y -= 18

    p.drawString(
        40,
        y,
        f"Fitness Level: {profile.activity_level}"
    )

    y -= 18

    p.drawString(
        40,
        y,
        f"Workout Location: {profile.workout_location}"
    )

    y -= 30

    # =============================
    # Fitness Plan
    # =============================

    for day in range(1, 16):

        exercises = FitnessPlanExercise.objects.filter(
            fitness_plan=active_plan,
            day_number=day
        )

        # Start a new page if needed
        if y < 120:
            p.showPage()
            y = 800

        # Day heading
        p.setFont("Helvetica-Bold", 13)
        p.drawString(
            40,
            y,
            f"Day {day}"
        )

        y -= 20

        # Rest day
        if not exercises.exists():

            p.setFont("Helvetica", 11)

            p.drawString(
                50,
                y,
                "Rest Day — Let your muscles recover."
            )

            y -= 20

            p.drawString(
                50,
                y,
                "Light walking or yoga is optional."
            )

            y -= 30

            continue

        # Exercises
        for exercise in exercises:

            # Check page space before each exercise
            if y < 100:
                p.showPage()
                y = 800

                p.setFont("Helvetica-Bold", 13)
                p.drawString(
                    40,
                    y,
                    f"Day {day} (continued)"
                )

                y -= 25

            p.setFont("Helvetica-Bold", 11)

            p.drawString(
                50,
                y,
                f"Exercise: {exercise.exercise_name}"
            )

            y -= 16

            p.setFont("Helvetica", 10)

            p.drawString(
                70,
                y,
                f"Duration: {exercise.duration_minutes} minutes"
            )

            y -= 15

            if exercise.sets and exercise.reps:

                p.drawString(
                    70,
                    y,
                    f"Sets: {exercise.sets}    "
                    f"Reps: {exercise.reps}"
                )

            else:

                p.drawString(
                    70,
                    y,
                    "Duration-based exercise"
                )

            y -= 15

            p.drawString(
                70,
                y,
                f"Estimated Calories Burned: "
                f"{exercise.calories_burned} kcal"
            )

            y -= 22

        y -= 10

    # =============================
    # Save PDF
    # =============================

    p.save()

    return response
