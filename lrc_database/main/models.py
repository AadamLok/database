import datetime
from xml.parsers.expat import model

import pytz
from django import forms
from django.contrib.auth.models import AbstractUser
from django.core import validators
from django.db import models
from django.db.models.query import QuerySet
from django.utils.translation import gettext_lazy as _

from .custom_validators import validate_course_number


class Course(models.Model):
    department = models.CharField(
        max_length=16,
        help_text="Department string, like COMPSCI or MATH.",
    )
    # Char field to accomodate for classes having letter in them like, "189C"
    number = models.CharField(
        max_length=10,
        validators=[validate_course_number],
        help_text="Course number, like the 189C in COMPSCI 189C.",
    )
    name = models.CharField(
        max_length=64,
        help_text='The human-legible name of the course, like "Programming with Data Structures."',
    )

    class Meta:
        ordering = ('department','number')

    def short_name(self):
        return f"{self.department} {self.number}"

    def __str__(self):
        return f"{self.department} {self.number}: {self.name}"

class Semester(models.Model):
    name = models.CharField(
        max_length=15,
        help_text="Name of the semester. like 'SPRING 2023'",
        primary_key=True,
        unique=True,
        null=False,
        blank=False
    )

    start_date = models.DateField(
        help_text="Classes start date. All the shifts of kind 'class' will be automatically created starting from this date.",
        null=False,
        blank=False
    )

    end_date = models.DateField(
        help_text="Classes end date. All the automatically created shifts from the semester will end on this date.",
        null=False,
        blank=False
    )

    active = models.BooleanField(
        help_text="Is this the currently active semester?",
        null=False,
        blank=False
    )

    def __str__(self):
        return self.name

class Holidays(models.Model):
    semester = models.ForeignKey(
        to=Semester,
        on_delete=models.CASCADE,
        blank=False,
        null=False
    )

    date = models.DateField(
        help_text="Date of holiday. All the shift on this date will be automatically deleted.",
        unique=True
    )

class DaySwitch(models.Model):
    semester = models.ForeignKey(
        to=Semester,
        on_delete=models.CASCADE,
        blank=False,
        null=False
    )

    date_of_switch = models.DateField(
        help_text="Date on which university is following some other days schedule.",
        unique=True
    )

    class Day(models.IntegerChoices):
        MONDAY = 0, "Monday"
        TUESDAY = 1, "Tuesday"
        WEDNESDAY = 2, "Wednesday"
        THURSDAY = 3, "Thurday"
        FRIDAY = 4, "Friday"
        SATURDAY = 5, "Saturday"
        SUNDAY = 6, "Sunday"

    day_to_follow = models.PositiveSmallIntegerField(
        choices=Day.choices,
        blank=False,
        null=False
    )

class FullCourse(models.Model):
    semester = models.ForeignKey(
        to=Semester,
        on_delete=models.CASCADE,
        blank=False,
        null=False
    )
    
    course = models.ForeignKey(
        to=Course,
        on_delete=models.CASCADE,
        blank=False,
        null=False,
        related_name="full_course_course_number",
        verbose_name="Full Course Detail"
    )

    faculty = models.CharField(
        max_length=100,
        help_text="Name of the faculty Member."
    )

    class Meta:
        unique_together = ('semester', 'course', 'faculty')
        ordering = ('semester', 'course', 'faculty')
    
    def __str__(self):
        return f"{self.semester}, {self.course.short_name()}, {self.faculty}"

    def short_name(self):
        return f"{self.course.short_name()}, {self.faculty}"


class ClassDetails(models.Model):
    full_course = models.ForeignKey(
        to=FullCourse,
        on_delete=models.CASCADE,
        blank=False,
        null=False
    )
    
    location = models.CharField(
        max_length=32,
        help_text="The location where the class will occur, e.g. GSMN 64.",
    )

    class Day(models.IntegerChoices):
        MONDAY = 0, "Monday"
        TUESDAY = 1, "Tuesday"
        WEDNESDAY = 2, "Wednesday"
        THURSDAY = 3, "Thurday"
        FRIDAY = 4, "Friday"
        SATURDAY = 5, "Saturday"
        SUNDAY = 6, "Sunday"

    class_day = models.PositiveSmallIntegerField(
        choices=Day.choices,
        help_text="Day of the class."
    )

    class_time = models.TimeField(
        help_text="Time of the class."
    )

    class_duration = models.DurationField(
        help_text="How long the class will last.",
    )

class LRCDatabaseUser(AbstractUser):
    first_name = models.CharField(_("first name"), max_length=100, blank=False)
    last_name = models.CharField(_("last name"), max_length=100, blank=False)
    email = models.EmailField(_("email"), max_length=100, blank=False)

    REQUIRED_FIELDS = [first_name, last_name, email]

    def is_privileged(self) -> bool:
        return self.groups.filter(name__in=("Office staff", "Supervisors")).exists()

    def __str__(self) -> str:
        if not (self.first_name and self.last_name):
            return self.username
        else:
            return f"{self.first_name} {self.last_name}"

class StaffUserPosition(models.Model):
    person = models.ForeignKey(
        to=LRCDatabaseUser,
        on_delete=models.CASCADE,
        help_text="The person whome you want to assign a position.",
        related_name="staff_for_user_position"
    )

    semester = models.ForeignKey(
        to=Semester,
        on_delete=models.CASCADE,
        help_text="Semester for which you are assigning this position."
    )

    position = models.CharField(
        max_length=5,
        choices=[("SI","SI"),("Tutor", "Tutor"),("PM", "PM")]
    )

    hourly_rate = models.DecimalField(
        help_text="Hourly rate for this position for this person.",
        decimal_places=2,
        max_digits=6
    )
    
    tutor_courses = models.ManyToManyField(
        Course, 
        blank=True, 
        default=None
    )

    si_course = models.ForeignKey(
        to=FullCourse,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        default=None,
        related_name="lrc_database_user_si_course",
        verbose_name="SI course",
    )

    peers = models.ManyToManyField(
        LRCDatabaseUser, 
        blank=True, 
        default=None,
        related_name="pm_staff_peers"
    )

    def peers_list(self):
        return self.peers.all()
    
    def str_peers_list(self):
        ret = ""
        for peer in self.peers_list():
            ret += ", " + str(peer)
        ret = ret[2:]
        return ret
    
    def assign_peer(self, peer):
        self.peers.add(peer)

    def tutor_courses_list(self):
        return self.tutor_courses.all()
    
    def str_tutor_courses_list(self):
        ret = ""
        for course in self.tutor_courses_list():
            ret += ", " + course.short_name()
        ret = ret[2:]
        return ret
    
    def assign_tutor_course(self, course):
        self.tutor_courses.add(course)


class Shift(models.Model):
    associated_person = models.ForeignKey(
        to=LRCDatabaseUser,
        on_delete=models.CASCADE,
        help_text="The person who is associated with this work shift.",
    )

    start = models.DateTimeField(help_text="The time that the shift starts.")

    duration = models.DurationField(help_text="How long the shift will last, in HH:MM:SS format.")

    location = models.CharField(
        max_length=32,
        help_text="The location where the shift will be occur, e.g. GSMN 64.",
    )

    kind = models.CharField(
        max_length=11,
        choices=(("SI", "SI"), ("Tutoring", "Tutoring"), ("Training", "Training"), ("Observation", "Observation"), ("Class", "Class")),
        help_text="The kind of shift this is: tutoring, SI, Training, Class, or Observation.",
    )

    class Meta:
        ordering = ('start',)

    @staticmethod
    def all_on_date(date: datetime.date) -> QuerySet["Shift"]:
        tz_adjusted_range_start = datetime.datetime(
            date.year, date.month, date.day, tzinfo=pytz.timezone("America/New_York")
        )
        tz_adjusted_range_end = tz_adjusted_range_start + datetime.timedelta(days=1)
        return Shift.objects.filter(
            start__gte=tz_adjusted_range_start,
            start__lte=tz_adjusted_range_end,
        )

    def __str__(self):
        tz = pytz.timezone("America/New_York")
        return f"{self.associated_person} in {self.location} at {self.start.astimezone(tz)} for {self.kind} Session"


class ShiftChangeRequest(models.Model):
    shift_to_update = models.ForeignKey(
        to=Shift,
        related_name="shift_change_request_target",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        default=None,
        help_text="Shift to edit. If none, this change request will create a new shift when approved.",
    )

    reason = models.CharField(
        max_length=512,
        help_text="Explanation for why this new shift or shift change is being requested.",
    )

    state = models.CharField(
        max_length=40,
        choices=(("Approved", "Approved"), ("Pending", "Pending"), ("Not Approved", "Not Approved"), ("New", "New")),
        help_text="The kind of shift this is.",
    )

    is_drop_request = models.BooleanField(default=False)

    new_associated_person = models.ForeignKey(
        to=LRCDatabaseUser,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        default=None,
        help_text="The person who is associated with this work shift.",
    )

    new_start = models.DateTimeField(
        blank=True,
        null=True,
        default=None,
        help_text="The date time that the shift starts if this request is approved.",
    )

    new_duration = models.DurationField(
        blank=True,
        null=True,
        default=None,
        help_text="How long the shift will last, in HH:MM:SS format, if this request is approved.",
    )

    new_location = models.CharField(
        max_length=32,
        blank=True,
        null=True,
        default=None,
        help_text="The location where this shift will occur, e.g. GSMN 64, if this request is approved.",
    )

    new_kind = models.CharField(
        max_length=11,
        choices=(("SI", "SI"), ("Tutoring", "Tutoring"), ("Training", "Training"), ("Observation", "Observation"), ("Class", "Class")),
        blank=True,
        null=True,
        default=None,
        help_text="The kind of shift this is: tutoring or SI.",
    )

    class Meta:
        ordering = ('new_start',)


class Hardware(models.Model):
    class Meta:
        verbose_name_plural = "hardware"

    name = models.CharField(max_length=200)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Loan(models.Model):
    target = models.ForeignKey(
        to=Hardware,
        related_name="intended_hardware_to_borrow",
        on_delete=models.CASCADE,
        help_text="REQUESTED HARDWARE",
    )

    hardware_user = models.ForeignKey(
        to=LRCDatabaseUser,
        on_delete=models.CASCADE,
        help_text="LRC USER",
    )

    start_time = models.DateTimeField(
        help_text="DD/MM/YYYY HH:MM",
    )

    return_time = models.DateTimeField(
        blank=True,
        null=True,
        default=None,
        help_text="DD/MM/YYYY HH:MM",
    )
