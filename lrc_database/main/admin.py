from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (
    Course,
    Semester,
    Holidays,
    DaySwitch,
    FullCourse,
    ClassDetails,
    LRCDatabaseUser,
    StaffUserPosition,
    Shift,
    ShiftChangeRequest,
    Hardware,
    Loan
)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = (
        "department",
        "number",
        "name"
    )
    ordering = (
        "department",
        "number"
    )

@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "start_date",
        "end_date",
        "active"
    )
    ordering = (
        "active",
        "start_date"
    )

@admin.register(Holidays)
class HolidaysAdmin(admin.ModelAdmin):
    list_display = (
        "semester",
        "date"
    )
    ordering = ("date","semester")

@admin.register(DaySwitch)
class DaySwitchAdmin(admin.ModelAdmin):
    list_display = (
        "semester",
        "date_of_switch",
        "day_to_follow"
    )
    ordering = ("date_of_switch","semester")

@admin.register(FullCourse)
class FullCourseAdmin(admin.ModelAdmin):
    list_display = (
        "semester",
        "course",
        "faculty"
    )
    ordering = ("semester", "course", "faculty")

@admin.register(ClassDetails)
class ClassDetalisAdmin(admin.ModelAdmin):
    list_display = (
        "full_course",
        "location",
        "class_day",
        "class_time",
        "class_duration"
    )
    ordering = ("full_course__semester","class_day")

@admin.register(LRCDatabaseUser)
class LRCDatabaseUserAdmin(UserAdmin):
    pass

@admin.register(StaffUserPosition)
class StaffUserPositionAdmin(admin.ModelAdmin):
    list_display = (
        "semester",
        "position",
        "person",
        "hourly_rate"
    )
    ordering = ("semester", "position", "person")

@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = (
        "position",
        "start",
        "duration",
        "kind"
    )
    ordering = ("start",)

@admin.register(ShiftChangeRequest)
class ShiftChangeRequestAdmin(admin.ModelAdmin):
    list_display = (
        "shift_to_update",
        "reason",
        "state",
        "is_drop_request"
    )
    ordering = ("new_start",)


@admin.register(Hardware)
class HardwareAdmin(admin.ModelAdmin):
    list_display = ("name", "is_available")
    ordering = ("name", "is_available")
    list_editable = ("is_available",)


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = (
        "target",
        "start_time",
        "return_time",
        "hardware_user",
    )
