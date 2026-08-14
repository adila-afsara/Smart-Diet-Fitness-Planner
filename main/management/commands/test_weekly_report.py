from django.core.management.base import BaseCommand
from main.models import User, UserProfile, DailyLog, BMIRecord, WeeklyReport, DietPlan
from main.agents import health_tracking_agent
from datetime import timedelta


class Command(BaseCommand):
    help = 'Test Day 7 progress report generation'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user_id',
            type=int,
            required=True,
            help='User ID to generate the test report for'
        )

    def handle(self, *args, **options):

        user_id = options['user_id']

        # --------------------------------------------------
        # 1. Get user
        # --------------------------------------------------
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User with ID {user_id} not found.')
            )
            return

        self.stdout.write(f'USER = {user.full_name}')

        # --------------------------------------------------
        # 2. Get profile
        # --------------------------------------------------
        try:
            profile = UserProfile.objects.get(user=user)
        except UserProfile.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('User profile not found.')
            )
            return

        # --------------------------------------------------
        # 3. Get active 15-day plan
        # --------------------------------------------------
        active_plan = DietPlan.objects.filter(
            user=user,
            plan_status='Active'
        ).first()

        if not active_plan:
            self.stdout.write(
                self.style.ERROR('No active diet plan found.')
            )
            return

        cycle_start = active_plan.plan_start_date
        cycle_end = cycle_start + timedelta(days=6)

        self.stdout.write(
            f'REPORT PERIOD = {cycle_start} to {cycle_end}'
        )

        # --------------------------------------------------
        # 4. Get Day 1 - Day 7 Daily Logs
        # --------------------------------------------------
        cycle_logs = DailyLog.objects.filter(
            user=user,
            log_date__gte=cycle_start,
            log_date__lte=cycle_end
        ).order_by('log_date')

        self.stdout.write(
            f'DAILY LOG COUNT = {cycle_logs.count()}'
        )

        if not cycle_logs.exists():
            self.stdout.write(
                self.style.ERROR(
                    'No daily logs found for the first 7 days.'
                )
            )
            return

        # --------------------------------------------------
        # 5. Get Day 1 - Day 7 BMI records
        # --------------------------------------------------
        cycle_bmis = BMIRecord.objects.filter(
            user=user,
            recorded_at__date__gte=cycle_start,
            recorded_at__date__lte=cycle_end
        ).order_by('recorded_at')

        self.stdout.write(
            f'BMI RECORD COUNT = {cycle_bmis.count()}'
        )

        # --------------------------------------------------
        # 6. Starting and ending weight
        # --------------------------------------------------
        first_log = cycle_logs.first()
        last_log = cycle_logs.last()

        starting_weight = first_log.current_weight
        ending_weight = last_log.current_weight

        weight_change = None

        if starting_weight is not None and ending_weight is not None:
            weight_change = ending_weight - starting_weight

        self.stdout.write(
            f'STARTING WEIGHT = {starting_weight}'
        )

        self.stdout.write(
            f'ENDING WEIGHT = {ending_weight}'
        )

        self.stdout.write(
            f'WEIGHT CHANGE = {weight_change}'
        )

        # --------------------------------------------------
        # 7. Starting and ending BMI
        # --------------------------------------------------
        starting_bmi = (
            cycle_bmis.first().bmi_value
            if cycle_bmis.exists()
            else None
        )

        ending_bmi = (
            cycle_bmis.last().bmi_value
            if cycle_bmis.exists()
            else None
        )

        self.stdout.write(
            f'STARTING BMI = {starting_bmi}'
        )

        self.stdout.write(
            f'ENDING BMI = {ending_bmi}'
        )

        # --------------------------------------------------
        # 8. Prepare user data for Health Tracking Agent
        # --------------------------------------------------
        user_data = {
            'starting_weight': starting_weight,
            'current_weight': ending_weight,
            'height': profile.height,
            'health_goal': profile.health_goal,
            'health_condition': profile.health_condition,
        }

        # --------------------------------------------------
        # 9. Prepare log data for Health Tracking Agent
        # --------------------------------------------------
        meal_follow_days = cycle_logs.filter(
            meal_followed=True
        ).count()

        exercise_days = cycle_logs.filter(
            exercise_completed=True
        ).count()

        avg_water = round(
            sum(
                float(log.water_intake_liters or 0)
                for log in cycle_logs
            ) / 7,
            2
        )

        agent_logs = {
            'meal_follow_days': meal_follow_days,
            'exercise_days': exercise_days,
            'avg_water': avg_water,
            'weight_change': round(
                float(weight_change),
                2
            ) if weight_change is not None else 0,
        }

        self.stdout.write(
            f'MEAL FOLLOW DAYS = {meal_follow_days}/7'
        )

        self.stdout.write(
            f'EXERCISE DAYS = {exercise_days}/7'
        )

        self.stdout.write(
            f'AVERAGE WATER = {avg_water} L/day'
        )

        # --------------------------------------------------
        # 10. Call Health Tracking Agent
        # --------------------------------------------------
        self.stdout.write(
            'Calling Health Tracking Agent...'
        )

        ai_report = health_tracking_agent(
            user_data,
            agent_logs
        )

        # --------------------------------------------------
        # 11. Save report into WeeklyReport table
        # --------------------------------------------------
        report, created = WeeklyReport.objects.update_or_create(
            user=user,
            week_start_date=cycle_start,
            week_end_date=cycle_end,
            defaults={
                'starting_weight': starting_weight,
                'ending_weight': ending_weight,
                'weight_change': weight_change,
                'starting_bmi': starting_bmi,
                'ending_bmi': ending_bmi,

                # Missing days count as failure.
                # Therefore denominator remains 7.
                'meal_follow_rate': round(
                    (meal_follow_days / 7) * 100
                ),

                'exercise_completion_rate': round(
                    (exercise_days / 7) * 100
                ),

                'ai_feedback': ai_report,
            }
        )

        # --------------------------------------------------
        # 12. Show result
        # --------------------------------------------------
        if created:
            self.stdout.write(
                self.style.SUCCESS(
                    'WEEKLY REPORT CREATED SUCCESSFULLY!'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    'WEEKLY REPORT UPDATED SUCCESSFULLY!'
                )
            )

        self.stdout.write(
            f'REPORT ID = {report.id}'
        )
