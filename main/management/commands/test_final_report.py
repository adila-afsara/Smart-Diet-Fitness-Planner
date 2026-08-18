from django.core.management.base import BaseCommand

from main.models import (
    User,
    UserProfile,
    DailyLog,
    BMIRecord,
    WeeklyReport,
    DietPlan,
)

from main.agents import health_tracking_agent

from datetime import timedelta


class Command(BaseCommand):

    help = 'Test final Day 1-Day 15 progress report generation'


    def add_arguments(self, parser):

        parser.add_argument(
            '--user_id',
            type=int,
            required=True,
            help='User ID to generate final report for'
        )


    def handle(self, *args, **options):

        user_id = options['user_id']


        # ==============================================
        # USER
        # ==============================================

        try:

            user = User.objects.get(
                id=user_id
            )

        except User.DoesNotExist:

            self.stdout.write(
                self.style.ERROR(
                    f'User with ID {user_id} not found.'
                )
            )

            return


        self.stdout.write(
            f'USER = {user.full_name}'
        )


        # ==============================================
        # PROFILE
        # ==============================================

        try:

            profile = UserProfile.objects.get(
                user=user
            )

        except UserProfile.DoesNotExist:

            self.stdout.write(
                self.style.ERROR(
                    'User profile not found.'
                )
            )

            return


        # ==============================================
        # ACTIVE DIET PLAN
        # ==============================================

        active_plan = DietPlan.objects.filter(
            user=user,
            plan_status='Active'
        ).first()


        if not active_plan:

            self.stdout.write(
                self.style.ERROR(
                    'No active diet plan found.'
                )
            )

            return


        cycle_start = (
            active_plan.plan_start_date
        )

        cycle_end = (
            cycle_start
            + timedelta(days=14)
        )


        self.stdout.write(
            f'FINAL REPORT PERIOD = '
            f'{cycle_start} to {cycle_end}'
        )


        # ==============================================
        # DAY 1 - DAY 15 LOGS
        # ==============================================

        cycle_logs = DailyLog.objects.filter(
            user=user,
            log_date__gte=cycle_start,
            log_date__lte=cycle_end
        ).order_by(
            'log_date'
        )


        self.stdout.write(
            f'DAILY LOG COUNT = '
            f'{cycle_logs.count()}'
        )


        if not cycle_logs.exists():

            self.stdout.write(
                self.style.ERROR(
                    'No daily logs found.'
                )
            )

            return


        # ==============================================
        # BMI RECORDS
        # ==============================================

        cycle_bmis = BMIRecord.objects.filter(
            user=user,
            recorded_at__date__gte=cycle_start,
            recorded_at__date__lte=cycle_end
        ).order_by(
            'recorded_at'
        )


        self.stdout.write(
            f'BMI RECORD COUNT = '
            f'{cycle_bmis.count()}'
        )


        # ==============================================
        # WEIGHT
        # ==============================================

        first_log = cycle_logs.first()
        last_log = cycle_logs.last()


        starting_weight = (
            first_log.current_weight
        )

        ending_weight = (
            last_log.current_weight
        )


        weight_change = None


        if (
            starting_weight is not None
            and ending_weight is not None
        ):

            weight_change = (
                ending_weight
                - starting_weight
            )


        self.stdout.write(
            f'STARTING WEIGHT = '
            f'{starting_weight}'
        )

        self.stdout.write(
            f'FINAL WEIGHT = '
            f'{ending_weight}'
        )

        self.stdout.write(
            f'TOTAL WEIGHT CHANGE = '
            f'{weight_change}'
        )


        # ==============================================
        # BMI
        # ==============================================

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


        # ==============================================
        # USER DATA
        # ==============================================

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


        # ==============================================
        # 15-DAY STATISTICS
        # ==============================================

        meal_follow_days = (
            cycle_logs.filter(
                meal_followed=True
            ).count()
        )


        exercise_days = (
            cycle_logs.filter(
                exercise_completed=True
            ).count()
        )


        avg_water = round(
            sum(
                float(
                    log.water_intake_liters
                    or 0
                )

                for log in cycle_logs
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

            'weight_change':
                round(
                    float(weight_change),
                    2
                )
                if weight_change is not None
                else 0,
        }


        self.stdout.write(
            f'MEAL FOLLOW DAYS = '
            f'{meal_follow_days}/15'
        )

        self.stdout.write(
            f'EXERCISE DAYS = '
            f'{exercise_days}/15'
        )

        self.stdout.write(
            f'AVERAGE WATER = '
            f'{avg_water} L/day'
        )


        # ==============================================
        # CALL AI
        # ==============================================

        self.stdout.write(
            'Calling Health Tracking Agent...'
        )


        ai_report = health_tracking_agent(
            user_data,
            agent_logs,
            report_days=15
        )


        # ==============================================
        # SAVE FINAL REPORT
        # ==============================================

        report, created = (
            WeeklyReport.objects.update_or_create(

                user=user,

                week_start_date=cycle_start,

                week_end_date=cycle_end,

                defaults={

                    'starting_weight':
                        starting_weight,

                    'ending_weight':
                        ending_weight,

                    'weight_change':
                        weight_change,

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
        )


        # ==============================================
        # RESULT
        # ==============================================

        if created:

            self.stdout.write(
                self.style.SUCCESS(
                    'FINAL 15-DAY REPORT '
                    'CREATED SUCCESSFULLY!'
                )
            )

        else:

            self.stdout.write(
                self.style.SUCCESS(
                    'FINAL 15-DAY REPORT '
                    'UPDATED SUCCESSFULLY!'
                )
            )


        self.stdout.write(
            f'REPORT ID = {report.id}'
        )
