from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_documenttemplatesetting_custom_signature'),
    ]

    operations = [
        migrations.AddField(
            model_name='documenttemplatesetting',
            name='border_style',
            field=models.CharField(
                choices=[('accent', 'Accent Color'), ('none', 'None')],
                default='accent',
                max_length=10,
            ),
        ),
    ]
