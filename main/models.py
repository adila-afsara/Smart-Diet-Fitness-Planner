from django.db import models
#database tables
# ── TABLE 1: Users ──
class User(models.Model):
    full_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name

    class Meta:
        db_table = 'users'


# ── TABLE 2: User Profiles ──
class UserProfile(models.Model):
    GENDER_CHOICES = [('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')]
    GOAL_CHOICES = [('Lose Weight', 'Lose Weight'), ('Gain Weight', 'Gain Weight'), ('Stay Healthy', 'Stay Healthy')]
    LEVEL_CHOICES = [('Beginner', 'Beginner'), ('Intermediate', 'Intermediate'), ('Advanced', 'Advanced')]
    LOCATION_CHOICES = [('Home', 'Home'), ('Gym', 'Gym')]
    CONDITION_CHOICES = [('None', 'None'), ('Diabetes', 'Diabetes'), ('High Blood Pressure', 'High Blood Pressure'), ('High Cholesterol', 'High Cholesterol')]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    age = models.IntegerField(null=True, blank=True)
    weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    height = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, null=True, blank=True)
    health_goal = models.CharField(max_length=20, choices=GOAL_CHOICES, null=True, blank=True)
    activity_level = models.CharField(max_length=20, choices=LEVEL_CHOICES, null=True, blank=True)
    workout_location = models.CharField(max_length=10, choices=LOCATION_CHOICES, null=True, blank=True)
    health_condition = models.CharField(max_length=30, choices=CONDITION_CHOICES, default='None')
    food_preferences = models.TextField(null=True, blank=True)
    avoid_foods = models.TextField(null=True, blank=True)
    weekly_budget = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.full_name}'s Profile"

    class Meta:
        db_table = 'user_profiles'


# ── TABLE 3: Diet Plans ──
class DietPlan(models.Model):
    STATUS_CHOICES = [('Active', 'Active'), ('Completed', 'Completed'), ('Expired', 'Expired')]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    plan_start_date = models.DateField()
    plan_end_date = models.DateField()
    total_daily_calories = models.IntegerField(null=True, blank=True)
    total_cost_bdt = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    plan_status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Active')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.full_name}'s Diet Plan"

    class Meta:
        db_table = 'diet_plans'


# ── TABLE 4: Diet Plan Meals ──
class DietPlanMeal(models.Model):
    MEAL_CHOICES = [('Breakfast', 'Breakfast'), ('Lunch', 'Lunch'), ('Dinner', 'Dinner'), ('Snack', 'Snack')]

    plan = models.ForeignKey(DietPlan, on_delete=models.CASCADE)
    day_number = models.IntegerField()
    meal_type = models.CharField(max_length=10, choices=MEAL_CHOICES)
    meal_name = models.CharField(max_length=255, null=True, blank=True)
    ingredients = models.TextField(null=True, blank=True)
    calories = models.IntegerField(null=True, blank=True)
    protein = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    carbs = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    fats = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    estimated_cost_bdt = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"Day {self.day_number} - {self.meal_type}"

    class Meta:
        db_table = 'diet_plan_meals'


# ── TABLE 5: Fitness Plans ──
class FitnessPlan(models.Model):
    STATUS_CHOICES = [('Active', 'Active'), ('Completed', 'Completed'), ('Expired', 'Expired')]
    LEVEL_CHOICES = [('Beginner', 'Beginner'), ('Intermediate', 'Intermediate'), ('Advanced', 'Advanced')]
    LOCATION_CHOICES = [('Home', 'Home'), ('Gym', 'Gym')]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    plan_start_date = models.DateField()
    plan_end_date = models.DateField()
    fitness_level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    workout_location = models.CharField(max_length=10, choices=LOCATION_CHOICES)
    plan_status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Active')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.full_name}'s Fitness Plan"

    class Meta:
        db_table = 'fitness_plans'


# ── TABLE 6: Fitness Plan Exercises ──
class FitnessPlanExercise(models.Model):
    fitness_plan = models.ForeignKey(FitnessPlan, on_delete=models.CASCADE)
    day_number = models.IntegerField()
    exercise_name = models.CharField(max_length=255, null=True, blank=True)
    duration_minutes = models.IntegerField(null=True, blank=True)
    sets = models.IntegerField(null=True, blank=True)
    reps = models.IntegerField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Day {self.day_number} - {self.exercise_name}"

    class Meta:
        db_table = 'fitness_plan_exercises'


# ── TABLE 7: Daily Logs ──
class DailyLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    log_date = models.DateField()
    current_weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    water_intake_liters = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    meal_followed = models.BooleanField(default=False)
    exercise_completed = models.BooleanField(default=False)
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.full_name} - {self.log_date}"

    class Meta:
        db_table = 'daily_logs'


# ── TABLE 8: BMI Records ──
class BMIRecord(models.Model):
    BMI_CHOICES = [('Underweight', 'Underweight'), ('Normal Weight', 'Normal Weight'), ('Overweight', 'Overweight'), ('Obese', 'Obese')]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    height = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    bmi_value = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    bmi_category = models.CharField(max_length=20, choices=BMI_CHOICES, null=True, blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.full_name} - BMI: {self.bmi_value}"

    class Meta:
        db_table = 'bmi_records'


# ── TABLE 9: Weekly Reports ──
class WeeklyReport(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    week_start_date = models.DateField(null=True, blank=True)
    week_end_date = models.DateField(null=True, blank=True)
    starting_weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    ending_weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    weight_change = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    starting_bmi = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    ending_bmi = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    meal_follow_rate = models.IntegerField(null=True, blank=True)
    exercise_completion_rate = models.IntegerField(null=True, blank=True)
    ai_feedback = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.full_name} - Report {self.week_start_date}"

    class Meta:
        db_table = 'weekly_reports'


# ── TABLE 10: Chatbot Conversations ──
class ChatbotConversation(models.Model):
    SENDER_CHOICES = [('User', 'User'), ('Bot', 'Bot')]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    sender = models.CharField(max_length=5, choices=SENDER_CHOICES)
    sent_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender}: {self.message[:50]}"

    class Meta:
        db_table = 'chatbot_conversations'


# ── TABLE 11: Dietitians ──
class Dietitian(models.Model):
    full_name = models.CharField(max_length=100)
    specialty = models.CharField(max_length=100, null=True, blank=True)
    hospital_clinic = models.CharField(max_length=255, null=True, blank=True)
    location = models.CharField(max_length=100, null=True, blank=True)
    consultation_fee_bdt = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    contact_number = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    available_days = models.CharField(max_length=100, null=True, blank=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return self.full_name

    class Meta:
        db_table = 'dietitians'