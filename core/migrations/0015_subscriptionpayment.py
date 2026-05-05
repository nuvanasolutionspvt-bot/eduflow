from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0014_schoolsubscription'),
    ]

    operations = [
        migrations.CreateModel(
            name='SubscriptionPayment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('receipt', models.CharField(max_length=40, unique=True)),
                ('order_id', models.CharField(max_length=100, unique=True)),
                ('payment_id', models.CharField(blank=True, max_length=100)),
                ('signature', models.CharField(blank=True, max_length=255)),
                ('amount', models.PositiveIntegerField()),
                ('currency', models.CharField(default='INR', max_length=3)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('verified', 'Verified'), ('failed', 'Failed')], default='pending', max_length=20)),
                ('notes_json', models.JSONField(blank=True, default=dict)),
                ('school', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='subscription_payments', to='core.school')),
                ('subscription', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='payments', to='core.schoolsubscription')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
