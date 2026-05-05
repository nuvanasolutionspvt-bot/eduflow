from datetime import timedelta

from django.utils import timezone

from .models import SchoolSetting, SchoolSubscription


def school_context(request):
    school = getattr(request, 'school', None)
    site_school = None
    school_subscription = None
    if school is not None:
        site_school = SchoolSetting.objects.filter(school=school).first()
        created_at = getattr(school, 'created_at', None) or timezone.now()
        trial_started_on = (
            timezone.localtime(created_at).date()
            if timezone.is_aware(created_at)
            else created_at.date()
        )
        school_subscription, _ = SchoolSubscription.objects.get_or_create(
            school=school,
            defaults={
                'trial_started_on': trial_started_on,
                'trial_expires_on': trial_started_on + timedelta(days=3),
                'annual_price': 5999,
            },
        )
    return {
        'site_school': site_school,
        'current_school': school,
        'school_subscription': school_subscription,
    }
