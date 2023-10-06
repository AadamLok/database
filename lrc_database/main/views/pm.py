from datetime import datetime, timedelta
from urllib import request

from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.utils import timezone

from ..forms import PMAddMeetingForm
from ..models import Shift, Course, StaffUserPosition, Semester
from . import restrict_to_groups, restrict_to_http_methods

User = get_user_model()

@login_required
@restrict_to_http_methods("GET")
def pm_schedule(request: HttpRequest, offset: int) -> HttpResponse:
	offset = int(offset)

	pm = get_object_or_404(User, id=request.user.id)
	if not pm.is_pm():
		raise PermissionDenied
    
	active_sem = Semester.objects.get_active_sem()

	positions = StaffUserPosition.objects.filter(
            person=pm,
            semester=active_sem,
            position="PM"
        ).all()
	
	today = timezone.localtime()
	start = today.replace(hour=0, minute=0, second=0)
	end = start + timedelta(days=7)
    
	info = {}
	courses = Course.objects.all()
    
	for pm_pos in positions:
		peers = pm_pos.peers_list()
		for peer in peers:
			courses = {}
			positions = StaffUserPosition.objects.filter(person=peer, semester=active_sem)
			for peer_pos in positions:
				if peer_pos.position == "SI":
					courses[peer_pos.si_course.course.short_name()] = \
						[peer_pos.si_course.course.id, [[],[],[],[],[],[],[]]]
				elif peer_pos.position == "Tutor":
					for course in peer_pos.tutor_courses_list():
						courses[course.short_name()] = \
							[course.id, [[],[],[],[],[],[],[]]]
			info[str(peer)] = [peer.id, courses]

		shifts = Shift.objects.filter(position__person__in=peers, start__gte=start, start__lte=end)
		weekdays = [start + timedelta(days=i) for i in range(7)]
		start_day = start.weekday()

		for shift in shifts:
			s_kind = shift.kind
			s_position = shift.position
			if s_kind == "SI":
				s_course = s_position.si_course.course
				info[str(s_position.person)][1][s_course.short_name()][1]\
					[(timezone.localtime(shift.start).weekday()-start_day)%7].append(shift)
			elif s_kind == "Tutoring":
				for course in s_position.tutor_courses_list():
					info[str(s_position.person)][1][course.short_name()][1]\
						[(timezone.localtime(shift.start).weekday()-start_day)%7].append(shift)

	context = {
        "offset": offset, 
        "weekdays": weekdays, 
        "info": info
    }

	return render(request, "pm/schedule.html", context)

@login_required
@restrict_to_http_methods("GET", "POST")
def pm_add_meeting(request: HttpRequest) -> HttpResponse:
	if request.method == "POST":
		pm_position = StaffUserPosition.objects.filter(
			person=request.user,
			semester=Semester.objects.get_active_sem(),
			position="PM"
		).first()
		form = PMAddMeetingForm(pm_position, request.POST)
		if not form.is_valid():
			messages.add_message(request, messages.ERROR, f"Form errors: {form.errors}")
			return redirect("pm_add_meeting")
		else:
			data = form.cleaned_data
			Shift.objects.create(
				position=data["position"],
				start=data["start"],
				duration=data["duration"],
				location=data["location"],
				kind="Meeting"
			)
			Shift.objects.create(
				position=pm_position,
				start=data["start"],
				duration=data["duration"],
				location=data["location"],
				kind="Meeting"
			)
			messages.add_message(request, messages.SUCCESS, f"Meeting successfully added!")
			return redirect("pm_add_meeting")
	else:
		pm_position = StaffUserPosition.objects.filter(
			person=request.user,
			semester=Semester.objects.get_active_sem(),
			position="PM"
		).first()
		form = PMAddMeetingForm(pm=pm_position)
		context = {"form":form}
		return render(request, "pm/add_meeting.html", context)