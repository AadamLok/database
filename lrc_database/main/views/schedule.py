from datetime import datetime, timedelta
from urllib import request

import pytz
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, get_object_or_404

from ..models import Shift, Course, StaffUserPosition
from . import restrict_to_groups, restrict_to_http_methods

timezone = pytz.timezone("America/New_York")
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
    offset = int(offset) if privileged else -7
    
    today = timezone.localize(datetime.combine(datetime.today(), datetime.min.time()))
    start = today + timedelta(days=offset)
    end = start + timedelta(days=7)

    shifts = Shift.objects.filter(start__gte=start.isoformat(), start__lte=end)

    weekdays = [start + i * timedelta(days=1) for i in range(7)]

    info = {}

    courses = Course.objects.all()

    for course in courses:
        info[course.short_name()] = [course.id, [[], [], [], [], [], [], []]]

    start_day = start.weekday()

    for shift in shifts:
        s_kind = shift.kind
        s_position = shift.position
        if s_kind == "SI" and (kind == "SI" or kind == "All"):
            s_course = s_position.si_course.course.short_name()
            info[s_course][1][(shift.start.weekday()-start_day)%7].append(shift)
        elif kind == "Tutoring" or kind == "All":
            for course in s_position.tutor_courses.all():
                info[course.short_name()][1][(shift.start.weekday()-start_day)%7].append(shift)
    
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
