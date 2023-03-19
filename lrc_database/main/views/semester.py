import json
from datetime import datetime
from typing import Any, Dict, Optional

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.core.exceptions import BadRequest, PermissionDenied
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_list_or_404, get_object_or_404, redirect, render
from django.urls import reverse
from django.db.models import Q

from ..forms import DaySwitchForm, HolidaysForm, SemesterForm, ReadOnlySemesterForm
from ..models import Semester, Holidays, DaySwitch
from . import personal, restrict_to_groups, restrict_to_http_methods

@login_required
@restrict_to_groups("Office staff", "Supervisors")
@restrict_to_http_methods("GET")
def list_semesters(request: HttpRequest) -> HttpResponse:
	semesters = Semester.objects.all()
	context = {"semesters":semesters}
	return render(request, "semester/list_semesters.html", context)

@login_required
@restrict_to_groups("Office staff", "Supervisors")
@restrict_to_http_methods("GET")
def change_active_semester(request: HttpRequest, name: str) -> HttpResponse:
	active_semester = Semester.objects.get_active_sem()

	if active_semester is None:
		sem = Semester.objects.filter(name=name).first()
		sem.active = True
		sem.save()
	elif active_semester.name == name:
		active_semester.active = False
		active_semester.save()
	else:
		active_semester.active = False
		sem = Semester.objects.filter(name=name).first()
		sem.active = True
		active_semester.save()
		sem.save()

	return redirect("list_semesters")


@login_required
@restrict_to_groups("Office staff", "Supervisors")
@restrict_to_http_methods("GET", "POST")
def add_semester(request: HttpRequest) -> HttpResponse:
	if request.method == "POST":
		form = SemesterForm(request.POST)

		if not form.is_valid():
			messages.add_message(request, messages.ERROR, f"Form errors: {form.errors}")
			return redirect("add_semester")
		
		data = form.cleaned_data

		Semester.objects.create(
			name=data["name"].upper(),
			start_date=data["start_date"],
			end_date=data["end_date"],
			active=False
		)

		return redirect("edit_semester", data["name"].upper())

	else:
		form = SemesterForm()
		context = {"sem_form": form}
		return render(request, "semester/add_semester.html", context)

@login_required
@restrict_to_groups("Office staff", "Supervisors")
@restrict_to_http_methods("GET", "POST")
def edit_semester(request: HttpRequest, name: str) -> HttpResponse:
	if request.method == "POST":
		if 'holiday_form' in request.POST:
			form = HolidaysForm(request.POST)
			sem = Semester.objects.filter(name=name).first()

			if not form.is_valid():
				messages.add_message(request, messages.ERROR, f"Form errors: {form.errors}")
				return redirect("edit_semester", name)
			
			data = form.cleaned_data

			Holidays.objects.create(
				semester=sem,
				date=data["date"]
			)

			messages.add_message(request, messages.SUCCESS, "Holiday successfully added.")
			return redirect("edit_semester", name)
		elif 'day_switch_form' in request.POST:
			form = DaySwitchForm(request.POST)
			sem = Semester.objects.filter(name=name).first()

			if not form.is_valid():
				messages.add_message(request, messages.ERROR, f"Form errors: {form.errors}")
				return redirect("edit_semester", name)
			
			data = form.cleaned_data

			DaySwitch.objects.create(
				semester=sem,
				date_of_switch=data["date_of_switch"],
				day_to_follow=data["day_to_follow"]
			)

			messages.add_message(request, messages.SUCCESS, "Day Switch successfully added.")
			return redirect("edit_semester", name)
	else:
		sem = Semester.objects.filter(name=name).first()
		holidays = Holidays.objects.filter(semester=sem).all()
		day_switch = DaySwitch.objects.filter(semester=sem).all()

		form_for_sem = ReadOnlySemesterForm(instance=sem)
		form_for_holiday = HolidaysForm()
		form_for_day_switch = DaySwitchForm()

		context = {
			"name":name, 
			"sem":sem, 
			"holidays":holidays, 
			"day_switch": day_switch, 
			"form_for_sem": form_for_sem,
			"form_for_holiday": form_for_holiday,
			"form_for_day_switch": form_for_day_switch
		}
		return render(request, "semester/edit_semester.html", context)

@restrict_to_groups("Office staff", "Supervisors")
def delete_holiday(request: HttpRequest, name: str, date: Any) -> HttpResponse:
    sem = Semester.objects.filter(name=name).first()
    Holidays.objects.filter(Q(semester=sem) & Q(date=date)).first().delete()
    messages.add_message(request, messages.SUCCESS, f"Successfully deleted holiday.")
    return redirect("edit_semester", name)


@restrict_to_groups("Office staff", "Supervisors")
def delete_day_switch(request: HttpRequest, name: str, date: Any) -> HttpResponse:
    sem = Semester.objects.filter(name=name).first()
    DaySwitch.objects.filter(Q(semester=sem) & Q(date_of_switch=date)).first().delete()
    messages.add_message(request, messages.SUCCESS, f"Successfully deleted day switch.")
    return redirect("edit_semester", name)
