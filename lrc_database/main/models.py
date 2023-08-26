import datetime

import pytz
from django import forms
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from django.core import validators
from django.db import models
from django.db.models.query import QuerySet
from django.utils.translation import gettext_lazy as _
from django.core.validators import FileExtensionValidator

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
        help_text="Course number, like the 198C in COMPSCI 198C.",
    )

    name = models.CharField(
        max_length=64,
        help_text='The human-legible name of the course, like "Programming with Data Structures."',
    )

    class Meta:
        ordering = ('department','number')

    def short_name(self):
        if self.department == "STUDY-SKILL":
            return "Study-Skill"
        return f"{self.department} {self.number}"

    def __str__(self):
        if self.department == "STUDY-SKILL":
            return "Study-Skill"
        return f"{self.department} {self.number}: {self.name}"

class CrossListed(models.Model):
    main_course = models.ForeignKey(
        to=Course,
        on_delete=models.CASCADE,
        blank=False,
        null=False
    )

    department = models.CharField(
        max_length=16,
        help_text="Department string, like COMPSCI or MATH.",
    )

    number = models.CharField(
        max_length=10,
        validators=[validate_course_number],
        help_text="Course number, like the 198C in COMPSCI 198C.",
    )

    name = models.CharField(
        max_length=64,
        help_text='The human-legible name of the course, like "Programming with Data Structures."',
    )

    def short_name(self):
        if self.department == "STUDY-SKILL":
            return "Study-Skill"
        return f"{self.department} {self.number}"

    def __str__(self):
        if self.department == "STUDY-SKILL":
            return "Study-Skill"
        return f"{self.department} {self.number}: {self.name}"

class SemesterManager(models.Manager):
    def get_active_sem(self):
        return self.filter(active=True).first()

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

    objects = SemesterManager()

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
        verbose_name="Course Code"
    )

    faculty = models.CharField(
        max_length=100,
        help_text="Name of the faculty Member."
    )

    class Meta:
        ordering = ('semester', 'course', 'faculty')
    
    def __str__(self):
        if FullCourse.objects.filter(semester=self.semester, course=self.course, faculty=self.faculty).count() == 1:
            return f"{self.semester}, {self.course.short_name()}, {self.faculty}"
        else:
            class_info = ClassDetails.objects.filter(full_course__id=self.id).all()
            class_str = ""
            for c in class_info:
                class_str += str(c) + " "
            return f"{self.semester}, {self.course.short_name()}, {self.faculty}, [{class_str}]"

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

    def __str__(self):
        class_start = self.class_time.strftime("%I:%M %p").lower()
        class_day = self.get_class_day_display()
        return f"{class_day} ({self.location}, {class_start})"

class LRCDatabaseUser(AbstractUser):
    first_name = models.CharField(_("first name"), max_length=100, blank=False)
    last_name = models.CharField(_("last name"), max_length=100, blank=False)
    email = models.EmailField(_("email"), max_length=100, blank=False, unique=True)

    REQUIRED_FIELDS = [first_name, last_name, email]

    class Meta:
        ordering = ('first_name','last_name','email')

    def is_privileged(self) -> bool:
        return self.groups.filter(name__in=("Office staff", "Supervisors")).exists()

    def is_si(self) -> bool:
        num_si_position = StaffUserPosition.objects.filter(person=self, semester=Semester.objects.get_active_sem(), position="SI").count()
        return num_si_position > 0
    
    def is_tutor(self) -> bool:
        num_tutor_position = StaffUserPosition.objects.filter(person=self, semester=Semester.objects.get_active_sem(), position="Tutor").count()
        return num_tutor_position > 0
    
    def is_gt(self) -> bool:
        num_gt_position = StaffUserPosition.objects.filter(person=self, semester=Semester.objects.get_active_sem(), position="GT").count()
        return num_gt_position > 0
    
    def is_ours_mentor(self) -> bool:
        num_om_position = StaffUserPosition.objects.filter(person=self, semester=Semester.objects.get_active_sem(), position="OursM").count()
        return num_om_position > 0
    
    def is_pm(self) -> bool:
        num_pm_position = StaffUserPosition.objects.filter(person=self, semester=Semester.objects.get_active_sem(), position="PM").count()
        return num_pm_position > 0

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name} [{self.email}]"

    def name(self) -> str:
        return f"{self.first_name} {self.last_name}"
    
    def str_last_name_first(self) -> str:
        return f"{self.last_name}, {self.first_name} [{self.email}]"

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
        choices=[("SI","SI"),("Tutor", "Tutor"),("PM", "PM"),("GT", "Group-Tutor"),("OursM", "OURS-Mentor"),("Tech","Tech"),("Other","Other")]
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
        verbose_name="SI/Group-Tutor course",
    )

    peers = models.ManyToManyField(
        LRCDatabaseUser, 
        blank=True, 
        default=None,
        related_name="pm_staff_peers"
    )

    class Meta:
        unique_together = ('person','semester', 'position', 'si_course')

    def __str__(self):
        if self.position == "SI" or self.position == "GT":
            return f"{self.position} - {self.si_course.course.short_name()}, {self.person.first_name} {self.person.last_name}"
        return f"{self.position}, {self.person.first_name} {self.person.last_name}"
    
    def str_pos(self):
        if self.position == "SI" or self.position == "GT":
            return f"{self.position} - {self.si_course.course.short_name()}"
        return f"{self.position}"
    
    def short_str(self):
        return f"{self.position}"

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

class ShiftManager(models.Manager):
    def filter(self, *args, **kwargs):
        return super().filter(*args, deleted=False, **kwargs)

    def all_on_date(self, date):
        tz_adjusted_range_start = datetime.datetime(
            date.year, date.month, date.day, tzinfo=pytz.timezone("America/New_York")
        )
        tz_adjusted_range_end = tz_adjusted_range_start + datetime.timedelta(days=1)
        return self.filter(
            start__gte=tz_adjusted_range_start,
            start__lte=tz_adjusted_range_end,
        )

    def add_class_shift(self, associated_postion, course):
        sem = course.semester
        
        classes = ClassDetails.objects.filter(full_course=course).all()
        holidays = Holidays.objects.filter(semester=sem).all()
        day_switch = DaySwitch.objects.filter(semester=sem).all()
        dates_of_switch = day_switch.values("date_of_switch")
        day_to_follow = day_switch.values("day_to_follow")

        shift_details = {
            "position": associated_postion,
            "kind": "Class"
        }

        for lecture in classes:
            days_ahead = (lecture.class_day - sem.start_date.weekday()) % 7
            class_date = sem.start_date + datetime.timedelta(days_ahead)

            shift_details["duration"] = lecture.class_duration
            shift_details["location"] = lecture.location
            shift_details["late_datetime"] = timezone.now()

            while class_date <= sem.end_date:
                if holidays.filter(date=class_date).exists() or dates_of_switch.filter(date_of_switch=class_date).exists():
                    class_date += datetime.timedelta(7)
                    continue
                
                shift_details["start"] = timezone.make_aware(datetime.datetime.combine(class_date, lecture.class_time))
                self.create(**shift_details)

                class_date += datetime.timedelta(7)
            
            for index, day in enumerate(day_to_follow):
                if day["day_to_follow"] == lecture.class_day:
                    shift_details["start"] = timezone.make_aware(datetime.datetime.combine(dates_of_switch[index]["date_of_switch"], lecture.class_time))
                    self.create(**shift_details)


class Shift(models.Model):
    position = models.ForeignKey(
        to=StaffUserPosition,
        on_delete=models.CASCADE,
        help_text="Which user and their possition is this shift for?"
    )

    start = models.DateTimeField(help_text="The time that the shift starts.")

    duration = models.DurationField(
        help_text="How long the shift will last. Format: HH:MM. E.g. if you want shift to be 1 hour 15 mins long, enter 01:15"
    )

    location = models.CharField(
        max_length=32,
        help_text="The location where the shift will be occur, e.g. GSMN 64.",
    )

    kind = models.CharField(
        max_length=14,
        choices=(("SI", "SI"), 
                 ("Tutoring", "Tutoring"),
                 ("Group Tutoring", "Group Tutoring"), 
                 ("Training", "Training"), 
                 ("Observation", "Observation"), 
                 ("Class", "Class"),
                 ("Preparation","Preparation"),
                 ("Meeting","Meeting"),
                 ("OURS Mentor", "OURS Mentor"),
                 ("Other","Other")),
        help_text="The kind of shift this is: tutoring, SI, Training, Class, or Observation.",
    )

    attended = models.BooleanField(
        default=False,
        null=False
    )

    signed = models.BooleanField(
        default=False,
        null=False
    )

    reason = models.CharField(
        max_length=500,
        help_text="Reason, if you were not able to attend your shift.",
        null=True,
        blank=True
    )

    late = models.BooleanField(
        default=False,
        null=False
    )

    late_datetime = models.DateTimeField(
        null=True,
        blank=True
    )

    deleted = models.BooleanField(
        default=False,
        null=False
    )

    document = models.FileField(
        upload_to="documents/", 
        validators=[FileExtensionValidator(allowed_extensions=["pdf"])],
        blank=True,
        null=True,
        default=None,
        help_text="Any pdf documnet you want to share for this shift."
    )

    objects = ShiftManager()

    class Meta:
        ordering = ('start',)

    def __str__(self):
        return f"{self.kind}, {self.location}"
    
    
    def str_long(self):
        return f"{self.kind}, {self.location}, {self.start}"


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

    new_position = models.ForeignKey(
        to=StaffUserPosition,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        default=None,
        help_text="The position that this shit is associated with this work shift.",
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
        max_length=14,
        choices=(
            ("SI", "SI"), 
            ("Tutoring", "Tutoring"),
            ("Group Tutoring", "Group Tutoring"), 
            ("Training", "Training"), 
            ("Observation", "Observation"), 
            ("Class", "Class"),
            ("Preparation","Preparation"),
            ("Meeting","Meeting"),
            ("OURS Mentor", "OURS Mentor"),
            ("Other","Other"),
        ),
        blank=True,
        null=True,
        default=None,
        help_text="The kind of shift this is: tutoring or SI.",
    )

    created = models.DateTimeField(
        auto_now_add=True,
        blank=True
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
