# Generated by Django 4.1.5 on 2023-03-13 15:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0004_alter_lrcdatabaseuser_email"),
    ]

    operations = [
        migrations.AlterField(
            model_name="shift",
            name="late_datetime",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
