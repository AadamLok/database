import csv
import random
from collections import defaultdict
from typing import DefaultDict
from datetime import date, datetime, timedelta, time

import pytz
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.utils import timezone
from faker import Faker
from main.models import Course, Hardware, LRCDatabaseUser, Shift, ShiftChangeRequest, FullCourse, Semester, ClassDetails, StaffUserPosition

User = get_user_model()


def create_superuser(net_id: str, password: str):
    print("Creating superuser...")
    User.objects.create_superuser(
        username=f"{net_id}+lrcadmin@umass.edu", 
        password=password, 
        email=f"{net_id}+lrcadmin@umass.edu", 
        first_name="Admin", 
        last_name=net_id
    )

def create_tech_user(net_id: str, password: str):
    print("Creating tech user...")
    user = User.objects.create_user(
        username=f"{net_id}+lrctech@umass.edu",
        password=password,
        email=f"{net_id}+lrctech@umass.edu",
        first_name="Tech",
        last_name=net_id,
    )

    supervisor_group = Group.objects.filter(name="Supervisors").first()
    supervisor_group.user_set.add(user)
    supervisor_group.save()

def create_groups():
    print("Creating groups...")
    group_names = ("Office staff", "Supervisors", "Staff")
    
    for group_name in group_names:
        Group.objects.create(name=group_name)

class Command(BaseCommand):
    """
    Sets up a database for final launch.
    Example:
        manage.py final_start_up_database
    """

    def add_arguments(self, parser) -> None:
        parser.add_argument("-a", "--add-user", action='store_true', default=False)
        parser.add_argument("--net-id", type=str)
        parser.add_argument("--password", type=str)

    def handle(self, *args, **options):
        have_email_and_pass = (options["net_id"] is not None) \
            and (options["password"] is not None)
        
        if not have_email_and_pass:
            print("""
                Wrong Use of command detected.

                If you want to setup the database just use the command with --net-id and --password arguments to create a superuser.

                If you just want to add a superuser, please use -a or --add-user flag with --net-id, and --password arguments.
            """)
            return None
        
        if '@' in options["net_id"]:
            print("""
                Wrong Use of command detected.

                net-id should not have @ in it. E.g. if you email is alokhandwala@umass.edu then you will use command like this --net-id alokhandwala
            """)

        if not options["add_user"]:
            create_groups()
            print("Database is ready to use!")
        create_superuser(
            options["net_id"],
            options["password"]
        )
        create_tech_user(
            options["net_id"],
            options["password"]
        )
        print("Superuser Added!")