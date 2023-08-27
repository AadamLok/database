# Generated by Django 4.1.7 on 2023-08-26 22:45

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0010_shiftchangerequest_created"),
    ]

    operations = [
        migrations.CreateModel(
            name="PunchedIn",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("start", models.DateTimeField(help_text="The time that the shift starts.")),
                (
                    "position",
                    models.ForeignKey(
                        help_text="Which user and their possition is this shift for?",
                        on_delete=django.db.models.deletion.CASCADE,
                        to="main.staffuserposition",
                    ),
                ),
            ],
            options={
                "ordering": ("start",),
            },
        ),
    ]
