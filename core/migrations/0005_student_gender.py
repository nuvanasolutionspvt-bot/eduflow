from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_student_address_mr_student_birth_place_mr_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='student',
            name='gender',
            field=models.CharField(
                blank=True,
                choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')],
                max_length=10,
            ),
        ),
    ]
