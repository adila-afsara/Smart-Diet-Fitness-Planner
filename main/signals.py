from allauth.account.signals import user_logged_in
from django.dispatch import receiver
from .models import User, UserProfile

@receiver(user_logged_in)
def bridge_social_login(request, user, **kwargs):
    email = user.email

    custom_user, created = User.objects.get_or_create(
        email=email,
        defaults={
            'full_name': user.get_full_name() or email.split('@')[0],
            'password': ''
        }
    )

    UserProfile.objects.get_or_create(
        user=custom_user,
        defaults={
            'age': 25,
            'weight': 60,
            'height': 165,
            'gender': 'Other',
            'health_goal': 'Stay Healthy',
            'health_condition': 'None',
            'activity_level': 'Beginner',
            'workout_location': 'Home',
            'weekly_budget': 1000,
            'location': 'Dhaka',
            'food_preferences': '',
            'avoid_foods': '',
        }
    )

    request.session['user_id'] = custom_user.id
    request.session['user_name'] = custom_user.full_name
