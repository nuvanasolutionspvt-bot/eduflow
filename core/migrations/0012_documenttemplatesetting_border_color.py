from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_documenttemplatesetting_border_style'),
    ]

    operations = [
        migrations.AddField(
            model_name='documenttemplatesetting',
            name='border_color',
            field=models.CharField(default='#cb0804', max_length=7),
        ),
    ]
