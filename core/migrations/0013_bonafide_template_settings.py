from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_documenttemplatesetting_border_color'),
    ]

    operations = [
        migrations.AlterField(
            model_name='documenttemplatesetting',
            name='border_style',
            field=models.CharField(
                choices=[
                    ('accent', 'Accent Color'),
                    ('double', 'Double'),
                    ('solid', 'Solid'),
                    ('dashed', 'Dashed'),
                    ('dotted', 'Dotted'),
                    ('none', 'None'),
                ],
                default='accent',
                max_length=10,
            ),
        ),
        migrations.AlterField(
            model_name='documenttemplatesetting',
            name='document_type',
            field=models.CharField(
                choices=[('bonafide', 'Bonafide'), ('hall-ticket', 'Hall Ticket')],
                max_length=40,
            ),
        ),
        migrations.AlterField(
            model_name='documenttemplatesetting',
            name='logo_position',
            field=models.CharField(
                choices=[
                    ('both', 'Both'),
                    ('left', 'Left'),
                    ('right', 'Right'),
                    ('center', 'Center'),
                    ('none', 'None'),
                ],
                default='both',
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name='documenttemplatesetting',
            name='border_width',
            field=models.PositiveSmallIntegerField(default=4),
        ),
        migrations.AddField(
            model_name='documenttemplatesetting',
            name='school_address',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='documenttemplatesetting',
            name='school_title',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='documenttemplatesetting',
            name='show_student_photo',
            field=models.BooleanField(default=True),
        ),
    ]
