# Generated by Django 4.1.7 on 2023-03-19 23:58

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0002_shift_deleted_alter_shift_duration"),
    ]

    operations = [
        migrations.AlterField(
            model_name="lrcdatabaseuser",
            name="email",
            field=models.EmailField(max_length=100, unique=True, verbose_name="email"),
        ),
    ]
