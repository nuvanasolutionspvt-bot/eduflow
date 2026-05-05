from datetime import timedelta

from django.db import migrations, models


def create_school_subscriptions(apps, schema_editor):
    School = apps.get_model('core', 'School')
    SchoolSubscription = apps.get_model('core', 'SchoolSubscription')

    for school in School.objects.all():
        started_on = school.created_at.date() if school.created_at else None
        if started_on is None:
            continue
        SchoolSubscription.objects.get_or_create(
            school=school,
            defaults={
                'trial_started_on': started_on,
                'trial_expires_on': started_on + timedelta(days=3),
                'annual_price': 5999,
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_bonafide_template_settings'),
    ]

    operations = [
        migrations.CreateModel(
            name='SchoolSubscription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('trial_started_on', models.DateField()),
                ('trial_expires_on', models.DateField()),
                ('free_downloads_used', models.PositiveIntegerField(default=0)),
                ('annual_price', models.PositiveIntegerField(default=5999)),
                ('annual_plan_started_on', models.DateField(blank=True, null=True)),
                ('annual_plan_expires_on', models.DateField(blank=True, null=True)),
                ('school', models.OneToOneField(on_delete=models.deletion.CASCADE, related_name='subscription', to='core.school')),
            ],
            options={
                'verbose_name': 'school subscription',
                'verbose_name_plural': 'school subscriptions',
            },
        ),
        migrations.RunPython(create_school_subscriptions, migrations.RunPython.noop),
    ]
