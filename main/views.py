from django.shortcuts import render, redirect, get_object_or_404
from .models import DailyLog, BMIRecord, WeeklyReport, DietPlan, ChatbotConversation
from .agents import chatbot_agent, quote_agent, json
from django.core.cache import cache
from datetime import date, timedelta
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

    # ==========================================================
    # LOGIN CHECK
    # ==========================================================

    if 'user_id' not in request.session:
        return redirect('login')

    user_id = request.session['user_id']

    user = get_object_or_404(
        User,
        id=user_id
    )


    # ==========================================================
    # IMPORT DASHBOARD MODELS
    # ==========================================================

    from .models import (
        UserProfile,
        DietPlan,
        DietPlanMeal,
        FitnessPlan,
        FitnessPlanExercise,
        DailyLog,
        BMIRecord,
        WeeklyReport,
    )

    from datetime import timedelta
    from decimal import Decimal
    from django.utils import timezone


    # ==========================================================
    # USER PROFILE
    # ==========================================================

    profile = UserProfile.objects.filter(
        user=user
    ).first()


    # ==========================================================
    # TODAY
    # ==========================================================

    today = timezone.localdate()

    now = timezone.localtime()

    current_hour = now.hour


    # Greeting
    if current_hour < 12:
        greeting = "Good Morning"

    elif current_hour < 17:
        greeting = "Good Afternoon"

    else:
        greeting = "Good Evening"


    formatted_date = today.strftime(
        "%A, %B %d, %Y"
    )


    # ==========================================================
    # ACTIVE DIET PLAN
    # ==========================================================

    active_diet_plan = DietPlan.objects.filter(
        user=user,
        plan_status='Active'
    ).order_by('-created_at').first()


    # Default
    current_day = 1


    if active_diet_plan:

        calculated_day = (
            today
            - active_diet_plan.plan_start_date
        ).days + 1


        # Keep dashboard cycle between Day 1 and Day 15
        current_day = max(
            1,
            min(calculated_day, 15)
        )


    days_done = current_day

    days_left = max(
        15 - current_day,
        0
    )


    # Cycle week
    if current_day <= 7:
        cycle_week = 1

    elif current_day <= 14:
        cycle_week = 2

    else:
        cycle_week = 3


    # ==========================================================
    # TODAY'S MEALS
    # ==========================================================

    todays_meals = []


    if active_diet_plan:

        todays_meals = list(
            DietPlanMeal.objects.filter(
                plan=active_diet_plan,
                day_number=current_day
            )
        )


        # Keep meals in a logical order
        meal_order = {
            "Breakfast": 1,
            "Lunch": 2,
            "Snack": 3,
            "Dinner": 4,
        }


        todays_meals.sort(
            key=lambda meal: meal_order.get(
                meal.meal_type,
                99
            )
        )


    # ==========================================================
    # TODAY'S MEAL COST
    # ==========================================================

    todays_meal_cost = Decimal("0.00")


    for meal in todays_meals:

        if meal.estimated_cost_bdt:

            todays_meal_cost += (
                meal.estimated_cost_bdt
            )


    # ==========================================================
    # DAILY BUDGET
    # ==========================================================

    daily_budget = None

    budget_difference = None

    budget_status = "Budget not set"


    if (
        profile
        and profile.weekly_budget
    ):

        daily_budget = (
            profile.weekly_budget
            / Decimal("7")
        )


        budget_difference = (
            daily_budget
            - todays_meal_cost
        )


        if budget_difference >= 0:

            budget_status = (
                f"৳ {budget_difference:.0f} "
                f"under daily budget"
            )

        else:

            budget_status = (
                f"৳ {abs(budget_difference):.0f} "
                f"over daily budget"
            )


    # ==========================================================
    # DAILY LOGS
    # ==========================================================

    all_logs = DailyLog.objects.filter(
        user=user
    ).order_by('log_date')


    today_log = DailyLog.objects.filter(
        user=user,
        log_date=today
    ).first()


    latest_weight_log = (
        DailyLog.objects.filter(
            user=user,
            current_weight__isnull=False
        )
        .order_by('-log_date')
        .first()
    )


    first_weight_log = (
        DailyLog.objects.filter(
            user=user,
            current_weight__isnull=False
        )
        .order_by('log_date')
        .first()
    )


    # ==========================================================
    # CURRENT WEIGHT
    # ==========================================================

    current_weight = None


    if latest_weight_log:

        current_weight = (
            latest_weight_log.current_weight
        )

    elif profile:

        current_weight = profile.weight


    # ==========================================================
    # WEIGHT CHANGE
    # ==========================================================

    weight_change = Decimal("0.00")

    weight_change_text = "No change recorded yet"


    if (
        first_weight_log
        and current_weight is not None
    ):

        weight_change = (
            current_weight
            - first_weight_log.current_weight
        )


        if weight_change < 0:

            weight_change_text = (
                f"↓ {abs(weight_change):.1f}kg "
                f"from start"
            )

        elif weight_change > 0:

            weight_change_text = (
                f"↑ {weight_change:.1f}kg "
                f"from start"
            )

        else:

            weight_change_text = (
                "No weight change from start"
            )


    # ==========================================================
    # BMI
    # ==========================================================

    latest_bmi = BMIRecord.objects.filter(
        user=user
    ).order_by(
        '-recorded_at'
    ).first()


    bmi_value = None

    bmi_category = "Not Available"


    if latest_bmi:

        bmi_value = latest_bmi.bmi_value

        bmi_category = (
            latest_bmi.bmi_category
            or "Not Available"
        )


    # If no BMI record exists yet,
    # calculate it for display only.
    elif (
        current_weight is not None
        and profile
        and profile.height
    ):

        height_m = (
            float(profile.height)
            / 100
        )


        if height_m > 0:

            bmi_value = round(
                float(current_weight)
                / (height_m ** 2),
                2
            )


            if bmi_value < 18.5:

                bmi_category = "Underweight"

            elif bmi_value < 25:

                bmi_category = "Normal Weight"

            elif bmi_value < 30:

                bmi_category = "Overweight"

            else:

                bmi_category = "Obese"


    # BMI message
    if bmi_category == "Normal Weight":

        bmi_message = (
            "You're in the normal BMI range."
        )

        bmi_badge_class = "badge-green"


    elif bmi_category == "Underweight":

        bmi_message = (
            "Your BMI is in the underweight range."
        )

        bmi_badge_class = "badge-orange"


    elif bmi_category == "Overweight":

        bmi_message = (
            "Your BMI is in the overweight range."
        )

        bmi_badge_class = "badge-orange"


    elif bmi_category == "Obese":

        bmi_message = (
            "Your BMI is in the obesity range."
        )

        bmi_badge_class = "badge-red"


    else:

        bmi_message = (
            "Add a daily log to calculate your BMI."
        )

        bmi_badge_class = "badge-yellow"


    # ==========================================================
    # CALORIE TARGET
    # ==========================================================

    calorie_target = 0


    if (
        active_diet_plan
        and active_diet_plan.total_daily_calories
    ):

        calorie_target = (
            active_diet_plan.total_daily_calories
        )


    calories_consumed = 0


    if (
        today_log
        and today_log.calories_consumed
    ):

        calories_consumed = (
            today_log.calories_consumed
        )


    if calorie_target:

        if calories_consumed == 0:

            calorie_status = (
                "Daily calorie goal"
            )

        elif calories_consumed <= calorie_target:

            calorie_status = (
                "On track today"
            )

        else:

            calorie_status = (
                "Above today's target"
            )

    else:

        calorie_status = (
            "No active calorie target"
        )


    # ==========================================================
    # WATER INTAKE
    # ==========================================================

    water_liters = 0.0


    if (
        today_log
        and today_log.water_intake_liters
    ):

        water_liters = float(
            today_log.water_intake_liters
        )


    # Your Progress page already treats
    # one glass as approximately 0.25L.
    water_target_liters = 2.0

    total_water_glasses = 8


    filled_water_glasses = min(
        int(
            water_liters / 0.25
        ),
        total_water_glasses
    )


    water_percentage = min(
        round(
            (
                water_liters
                / water_target_liters
            ) * 100
        ),
        100
    )


    # List for 8 glass icons in template
    water_glasses = []


    for glass_number in range(
        1,
        total_water_glasses + 1
    ):

        water_glasses.append(
            {
                "number": glass_number,

                "filled": (
                    glass_number
                    <= filled_water_glasses
                )
            }
        )


    # ==========================================================
    # ACTIVE FITNESS PLAN
    # ==========================================================

    active_fitness_plan = (
        FitnessPlan.objects.filter(
            user=user,
            plan_status='Active'
        )
        .order_by('-created_at')
        .first()
    )


    todays_exercises = []


    if active_fitness_plan:

        todays_exercises = list(
            FitnessPlanExercise.objects.filter(
                fitness_plan=active_fitness_plan,
                day_number=current_day
            )
        )


    exercise_total = len(
        todays_exercises
    )


    exercise_done = sum(
        1
        for exercise in todays_exercises
        if exercise.is_completed
    )


    # ==========================================================
    # THIS WEEK'S PROGRESS
    # ==========================================================

    week_start = (
        today
        - timedelta(
            days=today.weekday()
        )
    )


    week_end = (
        week_start
        + timedelta(days=6)
    )


    weekly_logs = DailyLog.objects.filter(
        user=user,
        log_date__gte=week_start,
        log_date__lte=week_end
    )


    meal_days = weekly_logs.filter(
        meal_followed=True
    ).count()


    exercise_days = weekly_logs.filter(
        exercise_completed=True
    ).count()


    water_goal_days = weekly_logs.filter(
        water_intake_liters__gte=Decimal("2.00")
    ).count()


    logged_days = weekly_logs.count()


    meal_percentage = round(
        (meal_days / 7) * 100
    )


    exercise_percentage = round(
        (exercise_days / 7) * 100
    )


    water_week_percentage = round(
        (water_goal_days / 7) * 100
    )


    log_percentage = round(
        (logged_days / 7) * 100
    )


    # ==========================================================
    # CYCLE TIMELINE
    # ==========================================================

    marker_days = sorted(
        set(
            [
                1,
                3,
                5,
                7,
                current_day,
                10,
                13,
                15
            ]
        )
    )


    cycle_markers = []


    for index, day_number in enumerate(
        marker_days
    ):

        if day_number < current_day:

            status = "done"

        elif day_number == current_day:

            status = "today"

        elif day_number == 15:

            status = "end"

        else:

            status = "mid"


        if day_number == current_day:

            label = "Today"

        elif day_number in [7, 15]:

            label = "Report"

        else:

            label = f"Day {day_number}"


        cycle_markers.append(
            {
                "day": day_number,

                "status": status,

                "label": label,

                "show_line": (
                    index
                    < len(marker_days) - 1
                ),

                "line_done": (
                    day_number
                    < current_day
                ),
            }
        )


    # ==========================================================
    # LATEST WEEKLY REPORT
    # ==========================================================

    latest_report = WeeklyReport.objects.filter(
        user=user
    ).order_by(
        '-week_start_date'
    ).first()


    # ==========================================================
    # MOTIVATION BANNER
    # ==========================================================

    motivation_title = (
        "Keep going! You're making progress! 🎉"
    )


    if current_day >= 7 and latest_report:

        motivation_text = (
            f"You are on Day {current_day} "
            f"of your 15-day plan. "
            f"Your latest progress report "
            f"is available."
        )


    elif weight_change < 0:

        motivation_text = (
            f"You are on Day {current_day} "
            f"of your plan and your recorded "
            f"weight has decreased by "
            f"{abs(weight_change):.1f} kg "
            f"from your first log."
        )


    elif weight_change > 0:

        motivation_text = (
            f"You are on Day {current_day} "
            f"of your plan. Your recorded "
            f"weight has changed by "
            f"{weight_change:.1f} kg "
            f"from your first log."
        )


    else:

        motivation_text = (
            f"You are currently on Day "
            f"{current_day} of your "
            f"15-day plan. Keep logging "
            f"your meals, activity and "
            f"progress consistently."
        )


    # ==========================================================
    # SEND EVERYTHING TO DASHBOARD
    # ==========================================================

    context = {

        # User
        "user": user,
        "profile": profile,


        # Header
        "greeting": greeting,
        "formatted_date": formatted_date,


        # Cycle
        "current_day": current_day,
        "days_done": days_done,
        "days_left": days_left,
        "cycle_week": cycle_week,
        "cycle_markers": cycle_markers,


        # Plans
        "active_diet_plan": active_diet_plan,
        "active_fitness_plan": active_fitness_plan,


        # Weight
        "current_weight": current_weight,
        "weight_change": weight_change,
        "weight_change_text": weight_change_text,


        # BMI
        "bmi_value": bmi_value,
        "bmi_category": bmi_category,
        "bmi_message": bmi_message,
        "bmi_badge_class": bmi_badge_class,


        # Calories
        "calorie_target": calorie_target,
        "calories_consumed": calories_consumed,
        "calorie_status": calorie_status,


        # Meals
        "todays_meals": todays_meals,
        "todays_meal_cost": todays_meal_cost,
        "daily_budget": daily_budget,
        "budget_difference": budget_difference,
        "budget_status": budget_status,


        # Today's log
        "today_log": today_log,


        # Water
        "water_liters": water_liters,
        "water_target_liters": water_target_liters,
        "filled_water_glasses": filled_water_glasses,
        "total_water_glasses": total_water_glasses,
        "water_percentage": water_percentage,
        "water_glasses": water_glasses,


        # Exercise
        "todays_exercises": todays_exercises,
        "exercise_total": exercise_total,
        "exercise_done": exercise_done,


        # Weekly progress
        "meal_days": meal_days,
        "exercise_days": exercise_days,
        "water_goal_days": water_goal_days,
        "logged_days": logged_days,

        "meal_percentage": meal_percentage,
        "exercise_percentage": exercise_percentage,
        "water_week_percentage": water_week_percentage,
        "log_percentage": log_percentage,


        # Weekly report
        "latest_report": latest_report,


        # Motivation
        "motivation_title": motivation_title,
        "motivation_text": motivation_text,
    }


    return render(
        request,
        'DietMate_dashboard_v2.html',
        context
    )

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

from datetime import date, timedelta
from decimal import Decimal
from django.shortcuts import redirect, render

from .models import BMIRecord, DailyLog, DietPlan

def progress(request):
    from decimal import Decimal
    from datetime import date, timedelta
    from .agents import health_tracking_agent
    from .models import WeeklyReport

    # =========================================================
    # LOGIN CHECK
    # =========================================================
    if 'user_id' not in request.session:
        return redirect('login')

    user_id = request.session['user_id']
    user = User.objects.get(id=user_id)

    try:
        profile = UserProfile.objects.get(user=user)
    except UserProfile.DoesNotExist:
        return redirect('dashboard')

    # =========================================================
    # REPORT / CYCLE SETUP
    # =========================================================
    weekly_reports = WeeklyReport.objects.filter(
        user=user
    ).order_by('-week_start_date')

    today = date.today()

    active_plan = DietPlan.objects.filter(
        user=user,
        plan_status='Active'
    ).first()

    cycle_day = None

    if active_plan:
        cycle_day = (
            today - active_plan.plan_start_date
        ).days + 1

        print("CYCLE DAY =", cycle_day)

        if cycle_day == 7:
            print(
                "DAY 7 REACHED — DAY 7 REPORT CAN BE GENERATED"
            )

        if cycle_day == 15:
            print(
                "DAY 15 REACHED — FINAL REPORT CAN BE GENERATED"
            )

    # =========================================================
    # SAVE / UPDATE TODAY'S DAILY LOG
    # =========================================================
    if request.method == 'POST':

        current_weight = request.POST.get(
            'current_weight'
        )

        water_glasses = request.POST.get(
            'water_glasses'
        )

        calories_consumed = request.POST.get(
            'calories_consumed'
        )

        meal_followed = (
            request.POST.get('meal_followed')
            == 'on'
        )

        exercise_completed = (
            request.POST.get('exercise_completed')
            == 'on'
        )

        feeling = request.POST.get(
            'feeling'
        )

        if current_weight:

            current_weight = Decimal(
                current_weight
            )

            # ---------------------------------------------
            # CONVERT WATER GLASSES TO LITERS
            # 1 glass ≈ 0.25L
            # ---------------------------------------------
            water_liters = None

            if water_glasses:

                water_liters = (
                    Decimal(water_glasses)
                    * Decimal('0.25')
                )

            # ---------------------------------------------
            # SAVE OR UPDATE TODAY'S LOG
            # ---------------------------------------------
            DailyLog.objects.update_or_create(
                user=user,
                log_date=today,
                defaults={
                    'current_weight':
                        current_weight,

                    'water_intake_liters':
                        water_liters,

                    'calories_consumed': (
                        int(calories_consumed)
                        if calories_consumed
                        else None
                    ),

                    'meal_followed':
                        meal_followed,

                    'exercise_completed':
                        exercise_completed,

                    'notes':
                        feeling,
                }
            )

            # =============================================
            # CALCULATE AND SAVE BMI
            # =============================================
            if profile.height:

                height_m = (
                    float(profile.height)
                    / 100
                )

                bmi_value = round(
                    float(current_weight)
                    / (height_m ** 2),
                    2
                )

                if bmi_value < 18.5:

                    bmi_category = (
                        'Underweight'
                    )

                elif bmi_value < 25:

                    bmi_category = (
                        'Normal Weight'
                    )

                elif bmi_value < 30:

                    bmi_category = (
                        'Overweight'
                    )

                else:

                    bmi_category = (
                        'Obese'
                    )

                # Keep only one BMI record
                # for the same day.
                BMIRecord.objects.filter(
                    user=user,
                    recorded_at__date=today
                ).delete()

                BMIRecord.objects.create(
                    user=user,
                    weight=current_weight,
                    height=profile.height,
                    bmi_value=bmi_value,
                    bmi_category=bmi_category
                )

        # Redirect to GET request.
        # Then Day 7 / Day 15 report generation
        # can use the newly saved log.
        return redirect('progress')

    # =========================================================
    # GENERAL PROGRESS DATA
    # =========================================================

    all_logs = DailyLog.objects.filter(
        user=user
    ).order_by(
        '-log_date'
    )

    all_bmi_records = BMIRecord.objects.filter(
        user=user
    ).order_by(
        '-recorded_at'
    )

    latest_log = all_logs.first()

    latest_bmi = (
        all_bmi_records.first()
    )

    first_log = all_logs.order_by(
        'log_date'
    ).first()

    # =========================================================
    # WEIGHT CHANGE SINCE FIRST LOG
    # =========================================================

    weight_change = None

    if (
        latest_log
        and first_log
        and latest_log != first_log
        and latest_log.current_weight
        is not None
        and first_log.current_weight
        is not None
    ):

        weight_change = (
            float(
                latest_log.current_weight
            )
            - float(
                first_log.current_weight
            )
        )

    # =========================================================
    # BMI CHANGE SINCE FIRST BMI RECORD
    # =========================================================

    bmi_change = None

    first_bmi = (
        all_bmi_records.order_by(
            'recorded_at'
        ).first()
    )

    if (
        latest_bmi
        and first_bmi
        and latest_bmi != first_bmi
        and latest_bmi.bmi_value
        is not None
        and first_bmi.bmi_value
        is not None
    ):

        bmi_change = (
            float(
                latest_bmi.bmi_value
            )
            - float(
                first_bmi.bmi_value
            )
        )

    # =========================================================
    # LAST 7 DAYS / WEEKLY PROGRESS
    # =========================================================

    week_start = (
        today
        - timedelta(days=6)
    )

    week_logs = all_logs.filter(
        log_date__gte=week_start
    )

    total_logs = (
        all_logs.count()
    )

    week_log_count = (
        week_logs.count()
    )

    exercise_done_count = (
        week_logs.filter(
            exercise_completed=True
        ).count()
    )

    meal_done_count = (
        week_logs.filter(
            meal_followed=True
        ).count()
    )

    exercise_rate = (
        round(
            (
                exercise_done_count
                / week_log_count
            ) * 100
        )
        if week_log_count
        else 0
    )

    meal_rate = (
        round(
            (
                meal_done_count
                / week_log_count
            ) * 100
        )
        if week_log_count
        else 0
    )

    # =========================================================
    # WATER TODAY
    # =========================================================

    water_today_glasses = None

    today_log = DailyLog.objects.filter(
        user=user,
        log_date=today
    ).first()

    if (
        today_log
        and today_log.water_intake_liters
    ):

        water_today_glasses = round(
            float(
                today_log.water_intake_liters
            )
            / 0.25
        )

    # =========================================================
    # WATER GOAL RATE
    # =========================================================

    water_goal_days = (
        week_logs.filter(
            water_intake_liters__gte=2.0
        ).count()
    )

    water_goal_rate = (
        round(
            (
                water_goal_days
                / week_log_count
            ) * 100
        )
        if week_log_count
        else 0
    )

    # =========================================================
    # DAY 7 REPORT
    # DAY 1 → DAY 7
    # =========================================================

    if (
        active_plan
        and cycle_day is not None
        and cycle_day >= 7
    ):

        day7_start = (
            active_plan.plan_start_date
        )

        day7_end = (
            day7_start
            + timedelta(days=6)
        )

        # ---------------------------------------------
        # CHECK IF DAY 7 REPORT ALREADY EXISTS
        # ---------------------------------------------

        existing_day7_report = (
            WeeklyReport.objects.filter(
                user=user,
                week_start_date=day7_start,
                week_end_date=day7_end
            ).first()
        )

        # Only generate automatically once.
        if not existing_day7_report:

            # -----------------------------------------
            # DAY 1 - DAY 7 LOGS
            # -----------------------------------------

            day7_logs = (
                DailyLog.objects.filter(
                    user=user,
                    log_date__gte=day7_start,
                    log_date__lte=day7_end
                ).order_by(
                    'log_date'
                )
            )

            # -----------------------------------------
            # DAY 1 - DAY 7 BMI
            # -----------------------------------------

            day7_bmis = (
                BMIRecord.objects.filter(
                    user=user,

                    recorded_at__date__gte=
                        day7_start,

                    recorded_at__date__lte=
                        day7_end

                ).order_by(
                    'recorded_at'
                )
            )

            # -----------------------------------------
            # MAKE SURE DAY 7 WAS LOGGED
            # -----------------------------------------

            day7_log_exists = (
                day7_logs.filter(
                    log_date=day7_end
                ).exists()
            )

            if (
                day7_logs.exists()
                and day7_log_exists
            ):

                first_cycle_log = (
                    day7_logs.first()
                )

                last_cycle_log = (
                    day7_logs.last()
                )

                # =====================================
                # WEIGHT
                # =====================================

                starting_weight = (
                    first_cycle_log.current_weight
                )

                ending_weight = (
                    last_cycle_log.current_weight
                )

                day7_weight_change = (
                    ending_weight
                    - starting_weight

                    if (
                        starting_weight
                        is not None

                        and ending_weight
                        is not None
                    )

                    else None
                )

                # =====================================
                # BMI
                # =====================================

                starting_bmi = (
                    day7_bmis.first().bmi_value

                    if day7_bmis.exists()

                    else None
                )

                ending_bmi = (
                    day7_bmis.last().bmi_value

                    if day7_bmis.exists()

                    else None
                )

                # =====================================
                # USER DATA FOR AI
                # =====================================

                user_data = {

                    'starting_weight':
                        starting_weight,

                    'current_weight':
                        ending_weight,

                    'height':
                        profile.height,

                    'health_goal':
                        profile.health_goal,

                    'health_condition':
                        profile.health_condition,
                }

                # =====================================
                # DAY 7 STATISTICS
                # =====================================

                meal_follow_days = (
                    day7_logs.filter(
                        meal_followed=True
                    ).count()
                )

                exercise_days = (
                    day7_logs.filter(
                        exercise_completed=True
                    ).count()
                )

                avg_water = round(
                    sum(
                        float(
                            log.water_intake_liters
                            or 0
                        )

                        for log
                        in day7_logs

                    ) / 7,

                    2
                )

                agent_logs = {

                    'meal_follow_days':
                        meal_follow_days,

                    'exercise_days':
                        exercise_days,

                    'avg_water':
                        avg_water,

                    'weight_change': (
                        round(
                            float(
                                day7_weight_change
                            ),
                            2
                        )

                        if day7_weight_change
                        is not None

                        else 0
                    ),
                }

                # =====================================
                # CALL HEALTH TRACKING AGENT
                # =====================================

                ai_report = (
                    health_tracking_agent(
                        user_data,
                        agent_logs,
                        report_days=7
                    )
                )

                print(
                    "DAY 7 HEALTH AGENT RESPONSE ="
                )

                print(
                    ai_report
                )

                # =====================================
                # SAVE DAY 7 REPORT
                # =====================================

                WeeklyReport.objects.update_or_create(

                    user=user,

                    week_start_date=
                        day7_start,

                    week_end_date=
                        day7_end,

                    defaults={

                        'starting_weight':
                            starting_weight,

                        'ending_weight':
                            ending_weight,

                        'weight_change':
                            day7_weight_change,

                        'starting_bmi':
                            starting_bmi,

                        'ending_bmi':
                            ending_bmi,

                        'meal_follow_rate':
                            round(
                                (
                                    meal_follow_days
                                    / 7
                                ) * 100
                            ),

                        'exercise_completion_rate':
                            round(
                                (
                                    exercise_days
                                    / 7
                                ) * 100
                            ),

                        'ai_feedback':
                            ai_report,
                    }
                )

                print(
                    "Day 7 progress report "
                    "generated successfully."
                )

    # =========================================================
    # DAY 15 FINAL REPORT
    # DAY 1 → DAY 15
    # =========================================================

    if (
        active_plan
        and cycle_day is not None
        and cycle_day >= 15
    ):

        final_start = (
            active_plan.plan_start_date
        )

        final_end = (
            final_start
            + timedelta(days=14)
        )

        # ---------------------------------------------
        # CHECK IF FINAL REPORT ALREADY EXISTS
        # ---------------------------------------------

        existing_final_report = (
            WeeklyReport.objects.filter(
                user=user,
                week_start_date=final_start,
                week_end_date=final_end
            ).first()
        )

        # Only generate automatically once.
        if not existing_final_report:

            # -----------------------------------------
            # DAY 1 - DAY 15 LOGS
            # -----------------------------------------

            final_logs = (
                DailyLog.objects.filter(
                    user=user,
                    log_date__gte=final_start,
                    log_date__lte=final_end
                ).order_by(
                    'log_date'
                )
            )

            # -----------------------------------------
            # DAY 1 - DAY 15 BMI RECORDS
            # -----------------------------------------

            final_bmis = (
                BMIRecord.objects.filter(
                    user=user,

                    recorded_at__date__gte=
                        final_start,

                    recorded_at__date__lte=
                        final_end

                ).order_by(
                    'recorded_at'
                )
            )

            # -----------------------------------------
            # MAKE SURE DAY 15 WAS LOGGED
            # -----------------------------------------

            final_day_log_exists = (
                final_logs.filter(
                    log_date=final_end
                ).exists()
            )

            if (
                final_logs.exists()
                and final_day_log_exists
            ):

                first_final_log = (
                    final_logs.first()
                )

                last_final_log = (
                    final_logs.last()
                )

                # =====================================
                # WEIGHT
                # =====================================

                starting_weight = (
                    first_final_log.current_weight
                )

                ending_weight = (
                    last_final_log.current_weight
                )

                final_weight_change = (
                    ending_weight
                    - starting_weight

                    if (
                        starting_weight
                        is not None

                        and ending_weight
                        is not None
                    )

                    else None
                )

                # =====================================
                # BMI
                # =====================================

                starting_bmi = (
                    final_bmis.first().bmi_value

                    if final_bmis.exists()

                    else None
                )

                ending_bmi = (
                    final_bmis.last().bmi_value

                    if final_bmis.exists()

                    else None
                )

                # =====================================
                # USER DATA FOR AI
                # =====================================

                user_data = {

                    'starting_weight':
                        starting_weight,

                    'current_weight':
                        ending_weight,

                    'height':
                        profile.height,

                    'health_goal':
                        profile.health_goal,

                    'health_condition':
                        profile.health_condition,
                }

                # =====================================
                # FULL 15-DAY STATISTICS
                # =====================================

                meal_follow_days = (
                    final_logs.filter(
                        meal_followed=True
                    ).count()
                )

                exercise_days = (
                    final_logs.filter(
                        exercise_completed=True
                    ).count()
                )

                avg_water = round(
                    sum(
                        float(
                            log.water_intake_liters
                            or 0
                        )

                        for log
                        in final_logs

                    ) / 15,

                    2
                )

                agent_logs = {

                    'meal_follow_days':
                        meal_follow_days,

                    'exercise_days':
                        exercise_days,

                    'avg_water':
                        avg_water,

                    'weight_change': (
                        round(
                            float(
                                final_weight_change
                            ),
                            2
                        )

                        if final_weight_change
                        is not None

                        else 0
                    ),
                }

                # =====================================
                # CALL HEALTH TRACKING AGENT
                # =====================================

                ai_report = (
                    health_tracking_agent(
                        user_data,
                        agent_logs,
                        report_days=15
                    )
                )

                print(
                    "FINAL 15-DAY HEALTH "
                    "AGENT RESPONSE ="
                )

                print(
                    ai_report
                )

                # =====================================
                # SAVE FINAL REPORT
                # =====================================

                WeeklyReport.objects.update_or_create(

                    user=user,

                    week_start_date=
                        final_start,

                    week_end_date=
                        final_end,

                    defaults={

                        'starting_weight':
                            starting_weight,

                        'ending_weight':
                            ending_weight,

                        'weight_change':
                            final_weight_change,

                        'starting_bmi':
                            starting_bmi,

                        'ending_bmi':
                            ending_bmi,

                        'meal_follow_rate':
                            round(
                                (
                                    meal_follow_days
                                    / 15
                                ) * 100
                            ),

                        'exercise_completion_rate':
                            round(
                                (
                                    exercise_days
                                    / 15
                                ) * 100
                            ),

                        'ai_feedback':
                            ai_report,
                    }
                )

                print(
                    "Final Day 1-Day 15 "
                    "progress report generated "
                    "successfully."
                )

    # =========================================================
    # CALORIES LOGGED RATE
    # =========================================================

    calories_logged_days = (
        week_logs.exclude(
            calories_consumed__isnull=True
        ).count()
    )

    calories_logged_rate = (
        round(
            (
                calories_logged_days
                / week_log_count
            ) * 100
        )

        if week_log_count

        else 0
    )

    # =========================================================
    # SIMPLE RULE-BASED FEEDBACK
    # =========================================================

    rates = {

        'meal plan':
            meal_rate,

        'exercise':
            exercise_rate,

        'water intake':
            water_goal_rate,
    }

    weakest_area = min(
        rates,
        key=rates.get
    )

    if total_logs == 0:

        ai_feedback = (
            "Log your first day to start "
            "getting personalized feedback here!"
        )

    elif rates[weakest_area] >= 80:

        ai_feedback = (
            "Excellent consistency across the board! "
            "Keep up the great work, especially with "
            f"your {weakest_area}."
        )

    else:

        ai_feedback = (
            "You're doing well overall — "
            "try focusing a bit more on your "
            f"{weakest_area}, it's at "
            f"{rates[weakest_area]}% right now. "
            "Small improvements add up!"
        )

    # =========================================================
    # RECENT LOG HISTORY
    # =========================================================

    recent_logs = list(
        all_logs[:8]
    )

    recent_logs.reverse()

    for log in recent_logs:

        matching_bmi = (
            BMIRecord.objects.filter(
                user=user,
                recorded_at__date=
                    log.log_date
            ).first()
        )

        log.bmi_display = (
            matching_bmi.bmi_value

            if matching_bmi

            else None
        )

    # =========================================================
    # WEIGHT TREND CHART
    # =========================================================

    chart_logs = list(
        all_logs.order_by(
            'log_date'
        )
    )

    if len(chart_logs) > 8:

        chart_logs = (
            chart_logs[-8:]
        )

    weight_chart_points = []

    weight_polyline = ""

    weight_area_path = ""

    weight_y_labels = []

    chart_start_weight = None

    chart_current_weight = None

    chart_weight_change = None

    chart_weight_change_abs = None

    # Only use logs that actually
    # contain a weight value.
    valid_chart_logs = [

        log

        for log in chart_logs

        if log.current_weight
        is not None
    ]

    if valid_chart_logs:

        weights = [

            float(
                log.current_weight
            )

            for log
            in valid_chart_logs
        ]

        min_w = min(
            weights
        )

        max_w = max(
            weights
        )

        if max_w == min_w:

            max_w = (
                min_w + 1
            )

        chart_left = 60

        chart_right = 380

        chart_top = 30

        chart_bottom = 155

        n = len(
            valid_chart_logs
        )

        for i, log in enumerate(
            valid_chart_logs
        ):

            w = float(
                log.current_weight
            )

            x = (

                chart_left

                if n == 1

                else chart_left
                + (
                    chart_right
                    - chart_left
                ) * (
                    i / (n - 1)
                )
            )

            y = (

                chart_bottom

                - (
                    (w - min_w)
                    / (
                        max_w - min_w
                    )
                ) * (
                    chart_bottom
                    - chart_top
                )
            )

            weight_chart_points.append(
                {
                    'x':
                        round(x, 1),

                    'y':
                        round(y, 1),

                    'weight':
                        w,

                    'date':
                        log.log_date,

                    'is_last':
                        (
                            i == n - 1
                        ),
                }
            )

        weight_polyline = " ".join(

            f"{point['x']},{point['y']}"

            for point
            in weight_chart_points
        )

        first_point = (
            weight_chart_points[0]
        )

        last_point = (
            weight_chart_points[-1]
        )

        path_parts = [

            f"M{first_point['x']},"
            f"{chart_bottom}"
        ]

        path_parts += [

            f"L{point['x']},"
            f"{point['y']}"

            for point
            in weight_chart_points
        ]

        path_parts += [

            f"L{last_point['x']},"
            f"{chart_bottom}",

            "Z",
        ]

        weight_area_path = (
            " ".join(
                path_parts
            )
        )

        weight_y_labels = [

            round(
                max_w,
                1
            ),

            round(
                max_w
                - (
                    max_w
                    - min_w
                ) / 3,
                1
            ),

            round(
                max_w
                - 2 * (
                    max_w
                    - min_w
                ) / 3,
                1
            ),

            round(
                min_w,
                1
            ),
        ]

        chart_start_weight = (
            weights[0]
        )

        chart_current_weight = (
            weights[-1]
        )

        chart_weight_change = round(

            chart_current_weight
            - chart_start_weight,

            1
        )

        chart_weight_change_abs = abs(
            chart_weight_change
        )

    # =========================================================
    # LATEST GENERATED REPORT
    # =========================================================

    latest_weekly_report = (
        WeeklyReport.objects.filter(
            user=user
        ).order_by(
            '-week_end_date'
        ).first()
    )

    latest_report_days = None

    latest_report_is_final = False

    if (
        latest_weekly_report

        and
        latest_weekly_report.week_start_date

        and
        latest_weekly_report.week_end_date
    ):

        latest_report_days = (
            latest_weekly_report.week_end_date
            - latest_weekly_report.week_start_date
        ).days + 1

        latest_report_is_final = (
            latest_report_days == 15
        )

    # =========================================================
    # SEND EVERYTHING TO TEMPLATE
    # =========================================================

    return render(
        request,
        'DietMate_progress.html',
        {
            'user':
                user,

            'profile':
                profile,

            'latest_log':
                latest_log,

            'latest_bmi':
                latest_bmi,

            'first_bmi':
                first_bmi,

            'all_bmi_records':
                all_bmi_records,

            'weight_change': (
                round(
                    weight_change,
                    1
                )

                if weight_change
                is not None

                else None
            ),

            'weight_change_abs': (
                round(
                    abs(
                        weight_change
                    ),
                    1
                )

                if weight_change
                is not None

                else None
            ),

            'bmi_change': (
                round(
                    bmi_change,
                    1
                )

                if bmi_change
                is not None

                else None
            ),

            'bmi_change_abs': (
                round(
                    abs(
                        bmi_change
                    ),
                    1
                )

                if bmi_change
                is not None

                else None
            ),

            'exercise_rate':
                exercise_rate,

            'meal_rate':
                meal_rate,

            'water_today_glasses':
                water_today_glasses,

            'recent_logs':
                recent_logs,

            'weight_chart_points':
                weight_chart_points,

            'weight_polyline':
                weight_polyline,

            'weight_area_path':
                weight_area_path,

            'weight_y_labels':
                weight_y_labels,

            'chart_start_weight':
                chart_start_weight,

            'chart_current_weight':
                chart_current_weight,

            'chart_weight_change':
                chart_weight_change,

            'chart_weight_change_abs':
                chart_weight_change_abs,

            'total_logs':
                total_logs,

            'today':
                today,

            'water_goal_rate':
                water_goal_rate,

            'calories_logged_rate':
                calories_logged_rate,

            'ai_feedback':
                ai_feedback,

            'week_log_count':
                week_log_count,

            'weekly_reports':
                weekly_reports,

            'latest_weekly_report':
                latest_weekly_report,

            'latest_report_days':
                latest_report_days,

            'latest_report_is_final':
                latest_report_is_final,

            'cycle_day':
                cycle_day,
        }
    )
def weekly_report(request, report_id):

    # =========================================================
    # LOGIN CHECK
    # =========================================================
    if 'user_id' not in request.session:
        return redirect('login')

    user_id = request.session['user_id']

    user = User.objects.get(
        id=user_id
    )

    # =========================================================
    # GET REPORT
    # =========================================================
    report = get_object_or_404(
        WeeklyReport,
        id=report_id,
        user=user
    )

    # =========================================================
    # DETERMINE REPORT TYPE
    # =========================================================
    report_days = (
        report.week_end_date
        - report.week_start_date
    ).days + 1

    # Day 1-Day 15 report
    if report_days == 15:

        is_final_report = True

        report_title = (
            "Final 15-Day Progress Report"
        )

        report_subtitle = (
            "Complete progress from "
            "Day 1 to Day 15"
        )

    # Day 1-Day 7 report
    else:

        is_final_report = False

        report_title = (
            "Day 7 Progress Report"
        )

        report_subtitle = (
            "Progress from "
            "Day 1 to Day 7"
        )

    # =========================================================
    # FORMAT AI FEEDBACK FROM MARKDOWN TO HTML
    # =========================================================

    import re

    from django.utils.html import escape

    from django.utils.safestring import (
        mark_safe
    )

    ai_text = (
        report.ai_feedback
        or ""
    )

    formatted_lines = []

    in_list = False

    # =========================================================
    # PROCESS AI RESPONSE LINE BY LINE
    # =========================================================

    for line in ai_text.splitlines():

        line = line.strip()

        # -----------------------------------------------------
        # SKIP HORIZONTAL SEPARATORS
        # -----------------------------------------------------

        if line in [
            "***",
            "---"
        ]:

            continue

        # -----------------------------------------------------
        # EMPTY LINE
        # -----------------------------------------------------

        if not line:

            if in_list:

                formatted_lines.append(
                    "</ul>"
                )

                in_list = False

            continue

        # -----------------------------------------------------
        # HEADING: ### Heading
        # -----------------------------------------------------

        if line.startswith(
            "### "
        ):

            if in_list:

                formatted_lines.append(
                    "</ul>"
                )

                in_list = False

            heading = escape(
                line[4:]
            )

            # Bold inside heading
            heading = re.sub(
                r"\*\*(.*?)\*\*",
                r"<strong>\1</strong>",
                heading
            )

            formatted_lines.append(
                f"<h3>{heading}</h3>"
            )

            continue

        # -----------------------------------------------------
        # BULLET: * something
        # -----------------------------------------------------

        if line.startswith(
            "* "
        ):

            if not in_list:

                formatted_lines.append(
                    "<ul>"
                )

                in_list = True

            content = escape(
                line[2:]
            )

            # Bold text
            content = re.sub(
                r"\*\*(.*?)\*\*",
                r"<strong>\1</strong>",
                content
            )

            # Italic text
            content = re.sub(
                r"\*(.*?)\*",
                r"<em>\1</em>",
                content
            )

            formatted_lines.append(
                f"<li>{content}</li>"
            )

            continue

        # -----------------------------------------------------
        # BULLET: - something
        # -----------------------------------------------------

        if line.startswith(
            "- "
        ):

            if not in_list:

                formatted_lines.append(
                    "<ul>"
                )

                in_list = True

            content = escape(
                line[2:]
            )

            content = re.sub(
                r"\*\*(.*?)\*\*",
                r"<strong>\1</strong>",
                content
            )

            content = re.sub(
                r"\*(.*?)\*",
                r"<em>\1</em>",
                content
            )

            formatted_lines.append(
                f"<li>{content}</li>"
            )

            continue

        # -----------------------------------------------------
        # NORMAL PARAGRAPH
        # -----------------------------------------------------

        if in_list:

            formatted_lines.append(
                "</ul>"
            )

            in_list = False

        content = escape(
            line
        )

        # Bold text: **text**
        content = re.sub(
            r"\*\*(.*?)\*\*",
            r"<strong>\1</strong>",
            content
        )

        # Italic text: *text*
        content = re.sub(
            r"\*(.*?)\*",
            r"<em>\1</em>",
            content
        )

        formatted_lines.append(
            f"<p>{content}</p>"
        )

    # =========================================================
    # CLOSE LIST IF AI RESPONSE ENDS WITH BULLET
    # =========================================================

    if in_list:

        formatted_lines.append(
            "</ul>"
        )

    # =========================================================
    # SAFE HTML FOR TEMPLATE
    # =========================================================

    ai_feedback_html = mark_safe(
        "\n".join(
            formatted_lines
        )
    )

    # =========================================================
    # SEND REPORT TO TEMPLATE
    # =========================================================

    return render(
        request,
        'DietMate_weekly_report.html',
        {
            'user':
                user,

            'report':
                report,

            'ai_feedback_html':
                ai_feedback_html,

            # Report information
            'report_days':
                report_days,

            'is_final_report':
                is_final_report,

            'report_title':
                report_title,

            'report_subtitle':
                report_subtitle,
        }
    )
def chatbot(request):

    # --------------------------------------------------
    # LOGIN CHECK
    # --------------------------------------------------

    if 'user_id' not in request.session:
        return redirect('login')

    user_id = request.session['user_id']
    user = get_object_or_404(User, id=user_id)

    profile = UserProfile.objects.get(user=user)

    # Get all daily logs in chronological order
    logs = DailyLog.objects.filter(
        user=user
    ).order_by('log_date')

    today = date.today()


    # --------------------------------------------------
    # PROGRESS DATA
    # --------------------------------------------------

    if logs.exists():

        # Number of different logged days
        current_day = logs.values(
            'log_date'
        ).distinct().count()

        # DietMate cycle is maximum 15 days
        current_day = min(current_day, 15)


        # -------------------------------
        # WEIGHT CHANGE
        # -------------------------------

        first_weight = logs.first().current_weight
        latest_weight = logs.last().current_weight

        if first_weight is not None and latest_weight is not None:

            # Positive number means weight lost
            weight_change = float(
                first_weight - latest_weight
            )

        else:
            weight_change = 0


        # -------------------------------
        # MEAL FOLLOW RATE
        # -------------------------------

        total_logs = logs.count()

        meals_followed = logs.filter(
            meal_followed=True
        ).count()

        meal_rate = round(
            (meals_followed / total_logs) * 100
        ) if total_logs else 0


        # -------------------------------
        # EXERCISE COMPLETION RATE
        # -------------------------------

        exercises_completed = logs.filter(
            exercise_completed=True
        ).count()

        exercise_rate = round(
            (exercises_completed / total_logs) * 100
        ) if total_logs else 0


    else:

        current_day = 0
        weight_change = 0
        meal_rate = 0
        exercise_rate = 0


    # --------------------------------------------------
    # LOGGED DATES
    # --------------------------------------------------

    logged_dates = set(
        logs.values_list(
            'log_date',
            flat=True
        )
    )


    # --------------------------------------------------
    # STREAK
    # --------------------------------------------------

    streak = 0

    # If today's Daily Log already exists,
    # start counting the streak from today.
    #
    # If today's log has NOT been submitted yet,
    # start from yesterday so the user's existing
    # streak does not disappear during the day.

    if today in logged_dates:

        check_date = today

    else:

        check_date = today - timedelta(days=1)


    # Count consecutive logged days backwards
    while check_date in logged_dates:

        streak += 1

        check_date -= timedelta(days=1)


    # --------------------------------------------------
    # WEEKLY STREAK DISPLAY
    # --------------------------------------------------

    # Get Monday of current week
    week_start = today - timedelta(
        days=today.weekday()
    )

    day_labels = [
        'M',
        'T',
        'W',
        'T',
        'F',
        'S',
        'S'
    ]

    streak_days = []


    for i in range(7):

        day_date = week_start + timedelta(
            days=i
        )


        # Today always gets the yellow highlight
        if day_date == today:

            css_class = 's-today'


        # Previous day that has a Daily Log
        elif day_date < today and day_date in logged_dates:

            css_class = 's-done'


        # Previous missed day or future day
        else:

            css_class = 's-miss'


        streak_days.append({

            'label': day_labels[i],

            'date': day_date,

            'css_class': css_class,

            'logged': day_date in logged_dates,
        })


    # --------------------------------------------------
    # MILESTONES
    # --------------------------------------------------

    milestones = [

        {
            'icon': '🏆',

            'name': 'First 7 Days Done!',

            'completed': current_day >= 7,

            'status': (
                'Unlocked on Day 7 🎉'

                if current_day >= 7

                else f'{7 - current_day} days remaining'
            )
        },


        {
            'icon': '⚖️',

            'name': 'Lost 0.5kg',

            'completed': weight_change >= 0.5,

            'status': (
                'Unlocked 🎉'

                if weight_change >= 0.5

                else
                f'{round(max(0.5 - weight_change, 0), 1)}kg more to go!'
            )
        },


        {
            'icon': '🏅',

            'name': 'Lost 1kg Total',

            'completed': weight_change >= 1,

            'status': (
                'Unlocked 🎉'

                if weight_change >= 1

                else
                f'{round(max(1 - weight_change, 0), 1)}kg more to go!'
            )
        },


        {
            'icon': '🎯',

            'name': 'Complete Full Cycle',

            'completed': current_day >= 15,

            'status': (
                'Unlocked 🎉'

                if current_day >= 15

                else
                f'{15 - current_day} days remaining'
            )
        }
    ]


    # --------------------------------------------------
    # MOOD TRACKER
    # --------------------------------------------------

    mood_options = [

        {
            'value': 'Amazing',
            'label': 'Amazing',
            'emoji': '😄'
        },

        {
            'value': 'Good',
            'label': 'Good',
            'emoji': '😊'
        },

        {
            'value': 'Okay',
            'label': 'Okay',
            'emoji': '😐'
        },

        {
            'value': 'Tired',
            'label': 'Tired',
            'emoji': '😔'
        },

        {
            'value': 'Stressed',
            'label': 'Stressed',
            'emoji': '😤'
        },
    ]


    valid_moods = {

        item['value']: item

        for item in mood_options
    }


    current_mood = request.session.get(
        'chatbot_mood',
        'Good'
    )


    if current_mood not in valid_moods:

        current_mood = 'Good'


    # --------------------------------------------------
    # POST ACTIONS
    # --------------------------------------------------

    if request.method == 'POST':

        action = request.POST.get(
            'action',
            'send_message'
        )


        # -------------------------------
        # CLEAR CHAT
        # -------------------------------

        if action == 'clear_chat':

            ChatbotConversation.objects.filter(
                user=user
            ).delete()

            return redirect('chatbot')


        # -------------------------------
        # SAVE MOOD
        # -------------------------------

        if action == 'set_mood':

            selected_mood = request.POST.get(
                'mood',
                ''
            )


            if selected_mood in valid_moods:

                request.session[
                    'chatbot_mood'
                ] = selected_mood


            return redirect('chatbot')


    # --------------------------------------------------
    # CURRENT MOOD DATA
    # --------------------------------------------------

    current_mood = request.session.get(
        'chatbot_mood',
        current_mood
    )


    current_mood_data = valid_moods.get(
        current_mood,
        valid_moods['Good']
    )


    # --------------------------------------------------
    # AI-GENERATED QUOTE
    # CACHED FOR 24 HOURS
    # --------------------------------------------------

    quote = cache.get(
        'daily_quote_bangladesh'
    )


    if not quote:

        try:

            raw_ai = quote_agent()

            clean = raw_ai.strip()


            # Remove Gemini markdown code block
            # if Gemini returns one
            if clean.startswith("```"):

                clean = clean.split("```")[1]


                if clean.startswith("json"):

                    clean = clean[4:]


            clean = clean.strip()


            # Convert Gemini JSON into Python dictionary
            quote = json.loads(clean)


            # Make sure quote exists
            if not quote.get('quote'):

                raise ValueError(
                    "Quote missing from AI response"
                )


            # Default author if Gemini did not provide one
            if not quote.get('author'):

                quote['author'] = (
                    'DietMate Health Tip'
                )


            # Cache quote for 24 hours
            cache.set(
                'daily_quote_bangladesh',
                quote,
                timeout=86400
            )


        except Exception as e:

            print(
                "QUOTE AGENT ERROR:",
                e
            )


            # Fallback quote
            quote = {

                'quote': (
                    "Take care of your body. "
                    "It's the only place you have to live."
                ),

                'author': 'Jim Rohn'
            }


    # --------------------------------------------------
    # CHAT HISTORY
    # --------------------------------------------------

    conversations = ChatbotConversation.objects.filter(
        user=user
    ).order_by(
        'sent_at'
    )


    # --------------------------------------------------
    # USER PROGRESS FOR CHATBOT AI
    # --------------------------------------------------

    user_progress = {

        'current_day': current_day,

        'weight_change': round(
            weight_change,
            2
        ),

        'meal_rate': meal_rate,

        'exercise_rate': exercise_rate,
    }


    # --------------------------------------------------
    # SEND CHAT MESSAGE
    # --------------------------------------------------

    if request.method == 'POST':

        action = request.POST.get(
            'action',
            'send_message'
        )


        if action == 'send_message':

            user_message = request.POST.get(
                'message',
                ''
            ).strip()


            if user_message:

                # Save user message
                ChatbotConversation.objects.create(

                    user=user,

                    message=user_message,

                    sender='User'
                )


                # Generate Gemini chatbot response
                bot_response = chatbot_agent(

                    user.full_name,

                    user_message,

                    user_progress
                )


                # Save chatbot response
                ChatbotConversation.objects.create(

                    user=user,

                    message=bot_response,

                    sender='Bot'
                )


            return redirect(
                'chatbot'
            )


    # --------------------------------------------------
    # QUICK REPLIES
    # --------------------------------------------------

    # Unicode escape codes are used so Windows/Python
    # does not convert the emojis into ????.

    quick_replies = [

        "\U0001F60A I feel great today!",

        "\U0001F4AA Motivate me!",

        "\U0001F371 What's for lunch?",

        "\U0001F4CA Show my progress",

        "\U0001F614 I missed a workout",

        "\U0001F4A7 Water reminder",
    ]


    # --------------------------------------------------
    # RENDER PAGE
    # --------------------------------------------------

    context = {

        # User
        'user': user,
        'profile': profile,


        # Progress
        'current_day': current_day,
        'weight_change': weight_change,
        'meal_rate': meal_rate,
        'exercise_rate': exercise_rate,


        # Streak
        'streak': streak,
        'streak_days': streak_days,


        # Milestones
        'milestones': milestones,


        # Quote
        'quote': quote,


        # Mood
        'mood_options': mood_options,
        'current_mood': current_mood,

        'current_mood_label':
            current_mood_data['label'],

        'current_mood_emoji':
            current_mood_data['emoji'],


        # Quick replies
        'quick_replies': quick_replies,


        # Chat history
        'conversations': conversations,
    }


    return render(
        request,
        'DietMate_chatbot.html',
        context
    )
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

def download_weekly_report(request, report_id):

    # =========================================================
    # LOGIN CHECK
    # =========================================================

    if 'user_id' not in request.session:
        return redirect('login')

    user = User.objects.get(
        id=request.session['user_id']
    )

    # =========================================================
    # GET REPORT
    # =========================================================

    report = get_object_or_404(
        WeeklyReport,
        id=report_id,
        user=user
    )

    # =========================================================
    # DETERMINE REPORT TYPE
    # =========================================================

    report_days = (
        report.week_end_date
        - report.week_start_date
    ).days + 1

    if report_days == 15:

        is_final_report = True

        pdf_title = (
            "Final 15-Day Progress Report"
        )

        pdf_filename = (
            "DietMate_Final_15_Day_Report.pdf"
        )

    else:

        is_final_report = False

        pdf_title = (
            "Day 7 Progress Report"
        )

        pdf_filename = (
            "DietMate_Day_7_Report.pdf"
        )

    # =========================================================
    # CREATE PDF RESPONSE
    # =========================================================

    response = HttpResponse(
        content_type='application/pdf'
    )

    response['Content-Disposition'] = (
        f'attachment; filename="{pdf_filename}"'
    )

    p = canvas.Canvas(response)

    # =========================================================
    # TITLE
    # =========================================================

    p.setFont(
        "Helvetica-Bold",
        18
    )

    p.drawCentredString(
        300,
        810,
        "DietMate BD"
    )

    p.setFont(
        "Helvetica-Bold",
        14
    )

    p.drawCentredString(
        300,
        788,
        pdf_title
    )

    # =========================================================
    # REPORT TYPE / PERIOD
    # =========================================================

    y = 750

    p.setFont(
        "Helvetica-Bold",
        12
    )

    p.drawString(
        40,
        y,
        "Report Information"
    )

    y -= 22

    p.setFont(
        "Helvetica",
        11
    )

    p.drawString(
        50,
        y,
        f"Name: {user.full_name}"
    )

    y -= 18

    p.drawString(
        50,
        y,
        (
            f"Report Period: "
            f"{report.week_start_date} "
            f"to {report.week_end_date}"
        )
    )

    y -= 18

    if is_final_report:

        p.drawString(
            50,
            y,
            "Cycle: Day 1 to Day 15"
        )

    else:

        p.drawString(
            50,
            y,
            "Cycle: Day 1 to Day 7"
        )

    y -= 30

    # =========================================================
    # WEIGHT PROGRESS
    # =========================================================

    p.setFont(
        "Helvetica-Bold",
        13
    )

    p.drawString(
        40,
        y,
        "Weight Progress"
    )

    y -= 22

    p.setFont(
        "Helvetica",
        11
    )

    p.drawString(
        50,
        y,
        (
            f"Starting Weight: "
            f"{report.starting_weight} kg"
        )
    )

    y -= 18

    p.drawString(
        50,
        y,
        (
            f"Ending Weight: "
            f"{report.ending_weight} kg"
        )
    )

    y -= 18

    # ---------------------------------------------------------
    # WEIGHT CHANGE DISPLAY
    # ---------------------------------------------------------

    if report.weight_change is not None:

        if report.weight_change < 0:

            weight_change_text = (
                f"Weight Lost: "
                f"{abs(float(report.weight_change)):.2f} kg"
            )

        elif report.weight_change > 0:

            weight_change_text = (
                f"Weight Gained: "
                f"{float(report.weight_change):.2f} kg"
            )

        else:

            weight_change_text = (
                "Weight Change: 0.00 kg"
            )

    else:

        weight_change_text = (
            "Weight Change: Not Available"
        )

    p.drawString(
        50,
        y,
        weight_change_text
    )

    y -= 30

    # =========================================================
    # BMI PROGRESS
    # =========================================================

    p.setFont(
        "Helvetica-Bold",
        13
    )

    p.drawString(
        40,
        y,
        "BMI Progress"
    )

    y -= 22

    p.setFont(
        "Helvetica",
        11
    )

    p.drawString(
        50,
        y,
        (
            f"Starting BMI: "
            f"{report.starting_bmi}"
        )
    )

    y -= 18

    p.drawString(
        50,
        y,
        (
            f"Ending BMI: "
            f"{report.ending_bmi}"
        )
    )

    y -= 30

    # =========================================================
    # PLAN CONSISTENCY
    # =========================================================

    p.setFont(
        "Helvetica-Bold",
        13
    )

    p.drawString(
        40,
        y,
        "Plan Consistency"
    )

    y -= 22

    p.setFont(
        "Helvetica",
        11
    )

    p.drawString(
        50,
        y,
        (
            f"Meal Plan Followed: "
            f"{report.meal_follow_rate}%"
        )
    )

    y -= 18

    p.drawString(
        50,
        y,
        (
            f"Exercise Completed: "
            f"{report.exercise_completion_rate}%"
        )
    )

    y -= 18

    p.drawString(
        50,
        y,
        (
            f"Report Duration: "
            f"{report_days} days"
        )
    )

    y -= 35

    # =========================================================
    # AI FEEDBACK
    # =========================================================

    p.setFont(
        "Helvetica-Bold",
        13
    )

    p.drawString(
        40,
        y,
        "AI Progress Feedback"
    )

    y -= 22

    p.setFont(
        "Helvetica",
        10
    )

    # Protect against empty AI feedback
    ai_feedback = (
        report.ai_feedback
        or "No AI feedback available."
    )

    feedback_lines = (
        ai_feedback.splitlines()
    )

    # =========================================================
    # HELPER FUNCTION FOR PAGE BREAK
    # =========================================================

    def check_new_page(
        current_y
    ):

        if current_y < 70:

            p.showPage()

            p.setFont(
                "Helvetica-Bold",
                13
            )

            p.drawString(
                40,
                800,
                "AI Progress Feedback (continued)"
            )

            p.setFont(
                "Helvetica",
                10
            )

            return 775

        return current_y

    # =========================================================
    # PRINT AI FEEDBACK
    # =========================================================

    import textwrap

    for line in feedback_lines:

        clean_line = (
            line.strip()
        )

        # Skip Markdown separators
        if clean_line in [
            "***",
            "---"
        ]:
            continue

        # Remove Markdown heading symbols
        clean_line = clean_line.replace(
            "### ",
            ""
        )

        clean_line = clean_line.replace(
            "## ",
            ""
        )

        clean_line = clean_line.replace(
            "# ",
            ""
        )

        # Remove bold Markdown
        clean_line = clean_line.replace(
            "**",
            ""
        )

        # Convert Markdown bullet
        if clean_line.startswith(
            "* "
        ):

            clean_line = (
                "- "
                + clean_line[2:]
            )

        elif clean_line.startswith(
            "- "
        ):

            clean_line = (
                "- "
                + clean_line[2:]
            )

        # Empty line creates some spacing
        if not clean_line:

            y -= 8

            y = check_new_page(
                y
            )

            continue

        # -----------------------------------------------------
        # WRAP LONG AI TEXT
        # -----------------------------------------------------

        wrapped_lines = textwrap.wrap(
            clean_line,
            width=90
        )

        if not wrapped_lines:

            wrapped_lines = [
                ""
            ]

        for wrapped_line in wrapped_lines:

            y = check_new_page(
                y
            )

            p.drawString(
                50,
                y,
                wrapped_line
            )

            y -= 15

    # =========================================================
    # FOOTER
    # =========================================================

    if y < 60:

        p.showPage()

        y = 800

    p.setFont(
        "Helvetica-Oblique",
        9
    )

    p.drawString(
        40,
        40,
        "Generated by DietMate BD"
    )

    # =========================================================
    # SAVE PDF
    # =========================================================

    p.save()

    return response
