# Generated by Django 4.1.7 on 2023-04-11 19:49

from django.db import migrations, models
import django.db.models.deletion
import main.custom_validators


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0008_alter_staffuserposition_position"),
    ]

    operations = [
        migrations.CreateModel(
            name="CrossListed",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("department", models.CharField(help_text="Department string, like COMPSCI or MATH.", max_length=16)),
                (
                    "number",
                    models.CharField(
                        help_text="Course number, like the 198C in COMPSCI 198C.",
                        max_length=10,
                        validators=[main.custom_validators.validate_course_number],
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        help_text='The human-legible name of the course, like "Programming with Data Structures."',
                        max_length=64,
                    ),
                ),
                ("main_course", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="main.course")),
            ],
        ),
    ]
