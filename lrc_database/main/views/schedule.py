from datetime import datetime, timedelta
from urllib import request

import pytz
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.core import serializers

from ..models import Shift, Course, StaffUserPosition, CrossListed, Semester, FullCourse
from . import restrict_to_groups, restrict_to_http_methods

User = get_user_model()


@login_required
@restrict_to_http_methods("GET", "POST")
# @restrict_to_groups("Office staff", "Supervisors")
def view_schedule(request: HttpRequest, kind: str, offset: str) -> HttpResponse:
    checked = False
    if request.method == "POST":
        if "few" in request.POST:
            checked = True
    user = get_object_or_404(User, id=request.user.id)
    privileged = user.is_privileged()
    offset = int(offset) if privileged else 0
    
    today = timezone.now().replace(hour=0, minute=0, second=0)
    start = today + timedelta(days=offset)
    end = start + timedelta(days=7)

    shifts = Shift.objects.filter(start__gte=start, start__lte=end)

    weekdays = [(start + i * timedelta(days=1)).replace(tzinfo=pytz.timezone("America/New_York")) for i in range(7)]

    info = {}

    courses = Course.objects.all()
    cross_listed = CrossListed.objects.all()

    cross_listed_dict = {}

    for course in courses:
        info[course.short_name()] = [course.id, [[], [], [], [], [], [], []]]
    for course in cross_listed:
        info[course.short_name()] = [course.main_course.id, [[], [], [], [], [], [], []]]
        if course.main_course.short_name() not in cross_listed_dict:
            cross_listed_dict[course.main_course.short_name()] = []
        cross_listed_dict[course.main_course.short_name()].append(course)
        
    start_day = start.weekday()

    for shift in shifts:
        s_kind = shift.kind
        s_position = shift.position
        if (s_kind == "SI" or s_kind == "GT") and (kind == "SI" or kind == "All"):
            s_course = s_position.si_course.course.short_name()
            exam_rev = shift.duration > timedelta(hours=1,minutes=15)
            info[s_course][1][(timezone.localtime(shift.start).weekday()-start_day)%7].append({"shift":shift,"exam_rev":exam_rev})
        elif s_kind == "Tutoring" and (kind == "Tutoring" or kind == "All"):
            for course in s_position.tutor_courses.all():
                info[course.short_name()][1][(timezone.localtime(shift.start).weekday()-start_day)%7].append({"shift":shift,"exam_rev":False})
    
    for main_course in cross_listed_dict:
        for course in cross_listed_dict[main_course]:
            info[course.short_name()][1] = info[main_course][1]

    if checked:
        for name in list(info):
            for day_info in info[name][1]:
                if len(day_info) > 0:
                    break
            else:
                del info[name]

    context = {
        "privileged": privileged, 
        "kind": kind, 
        "offset": offset, 
        "weekdays": weekdays, 
        "info": info,
        "checked": checked
    }

    return render(request, "schedule/schedule_view.html", context)


@restrict_to_http_methods("GET")
def api_schedule(request: HttpRequest, kind: str) -> JsonResponse:
    offset = 0
    today = timezone.now()
    start = today + timedelta(days=offset)
    end = start + timedelta(days=7)

    shifts = Shift.objects.filter(start__gte=start.isoformat(), start__lte=end)

    weekdays = [start + i * timedelta(days=1) for i in range(7)]
    weekdays = [[day.weekday(), day.strftime("%m/%d")] for day in weekdays]

    info = {}

    courses = Course.objects.all()
    cross_listed = CrossListed.objects.all()

    cross_listed_dict = {}

    for course in courses:
        info[course.short_name()] = [course.id, [[], [], [], [], [], [], []]]

    for course in cross_listed:
        info[course.short_name()] = [course.main_course.id, [[], [], [], [], [], [], []]]
        if course.main_course.short_name() not in cross_listed_dict:
            cross_listed_dict[course.main_course.short_name()] = []
        cross_listed_dict[course.main_course.short_name()].append(course)

    start_day = start.weekday()

    for shift in shifts:
        s_kind = shift.kind
        s_position = shift.position
        
        faculty = None
        if s_kind == "SI":
            faculty = shift.position.si_course.faculty
            faculty = "All Sections" if faculty[0] == "*" else faculty
        start_time = shift.start.strftime("%I:%M %p").lower()
        end_time = (shift.start+shift.duration).strftime("%I:%M %p").lower()
        shift_dict = {
            "faculty": faculty,
            "location": shift.location,
            "time": f"{start_time} - {end_time}",
            "person": shift.position.person.name(),
            "exam_rev": shift.duration > timedelta(hours=1, minutes=15)
        }
        
        if (s_kind == "SI" or s_kind == "Group Tutoring") and (kind == "SI" or kind == "All"):
            s_course = s_position.si_course.course.short_name()
            info[s_course][1][(timezone.localtime(shift.start).weekday()-start_day)%7].append(shift_dict)
        elif kind == "Tutoring" or kind == "All":
            for course in s_position.tutor_courses.all():
                info[course.short_name()][1][(timezone.localtime(shift.start).weekday()-start_day)%7].append(shift_dict)

    si_courses = StaffUserPosition.objects.filter(semester=Semester.objects.get_active_sem(), position__in=["SI","GT"]).values_list("si_course")
    si_courses = list(FullCourse.objects.filter(id__in=si_courses).values_list("course", flat=True))
    for main_course in cross_listed_dict:
        for course in cross_listed_dict[main_course]:
            info[course.short_name()][1] = info[main_course][1]
    
    keys = list(info.keys())
    for course in keys:
        if info[course][0] not in si_courses:
            del info[course]

    info = dict(sorted(info.items()))

    context = {
        "kind": kind, 
        "offset": offset, 
        "weekdays": weekdays, 
        "info": info
    }

    return JsonResponse(context)