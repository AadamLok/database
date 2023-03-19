from datetime import date, datetime

import pytz
from django import forms
from django.contrib import messages
from django.core.exceptions import BadRequest
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from ..models import Shift
from . import restrict_to_groups, restrict_to_http_methods


class DropShiftsOnDateForm(forms.Form):
    date = forms.DateField(
        help_text="MM/DD/YYYY", 
        widget = forms.widgets.DateInput(attrs={'type': 'date'}),
    )


@restrict_to_groups("Office staff", "Supervisors")
@restrict_to_http_methods("GET")
def drop_shifts_on_date(request: HttpRequest) -> HttpResponse:
    form = DropShiftsOnDateForm()
    return render(request, "shifts/drop_shifts_on_date.html", {"form": form})


@restrict_to_groups("Office staff", "Supervisors")
@restrict_to_http_methods("GET", "POST")
def drop_shifts_on_date_confirmation(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = DropShiftsOnDateForm(request.POST)
        if not form.is_valid():
            messages.add_message(request, messages.ERROR, f"Form has errors: {form.errors}")
            return redirect("drop_shifts_on_date")
        date = form.cleaned_data["date"]
        shifts = Shift.objects.filter(start__year=date.year, start__month=date.month, start__day=date.day)
        request.session["shift_keys"] = list(shifts.values_list("id", flat=True))
        return render(request, "shifts/drop_shifts_on_date_confirmation.html", {"affected_shifts": shifts})
    else:
        shift_keys = request.session.get("shift_keys", [])
        shifts = Shift.objects.filter(id__in=shift_keys)
        deleted_count, _ = shifts.delete()
        messages.add_message(request, messages.INFO, f"Deleted {deleted_count} shifts.")
        return redirect("drop_shifts_on_date")


class SwapShiftDates(forms.Form):
    first_date = forms.DateField(
        help_text="MM/DD/YYYY", 
        widget = forms.widgets.DateInput(attrs={'type': 'date'}),
    )
    second_date = forms.DateField(
        help_text="MM/DD/YYYY", 
        widget = forms.widgets.DateInput(attrs={'type': 'date'}),
    )


@restrict_to_groups("Office staff", "Supervisors")
@restrict_to_http_methods("GET")
def swap_shift_dates(request: HttpRequest) -> HttpResponse:
    form = SwapShiftDates()
    return render(request, "shifts/swap_shift_dates.html", {"form": form})


@restrict_to_groups("Office staff", "Supervisors")
@restrict_to_http_methods("GET", "POST")
def swap_shift_dates_confirmation(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = SwapShiftDates(request.POST)
        if not form.is_valid():
            messages.add_message(request, messages.ERROR, f"Form has errors: {form.errors}")
            return redirect("swap_shift_dates")
        first_date = form.cleaned_data["first_date"]
        second_date = form.cleaned_data["second_date"]

        first_date_shifts = Shift.objects.all_on_date(first_date)
        second_date_shifts = Shift.objects.all_on_date(second_date)

        return render(
            request,
            "shifts/swap_shift_dates_confirmation.html",
            {
                "first_date": first_date,
                "first_date_shifts": first_date_shifts,
                "second_date": second_date,
                "second_date_shifts": second_date_shifts,
            },
        )

    else:  # request.method == "GET"
        first_date = date.fromisoformat(request.GET["first"])
        second_date = date.fromisoformat(request.GET["second"])

        first_date_shifts = Shift.objects.all_on_date(first_date)
        second_date_shifts = Shift.objects.all_on_date(second_date)

        for shift in first_date_shifts:
            start = shift.start.astimezone(pytz.timezone("America/New_York"))
            start = start.replace(
                year=second_date.year,
                month=second_date.month,
                day=second_date.day,
            )
            shift.start = start
            shift.save()

        for shift in second_date_shifts:
            start = shift.start.astimezone(pytz.timezone("America/New_York"))
            start = start.replace(
                year=first_date.year,
                month=first_date.month,
                day=first_date.day,
            )
            shift.start = start
            shift.save()

        messages.add_message(
            request, messages.INFO, f"Swapped dates for {(first_date_shifts | second_date_shifts).count()} shifts."
        )
        return redirect("swap_shift_dates")


class MoveShiftsFromDateForm(forms.Form):
    from_ = forms.DateField(
        help_text="MM/DD/YYYY", 
        widget = forms.widgets.DateInput(attrs={'type': 'date'}),
    )
    to_ = forms.DateField(
        help_text="MM/DD/YYYY", 
        widget = forms.widgets.DateInput(attrs={'type': 'date'}),
    )


@restrict_to_groups("Office staff", "Supervisors")
@restrict_to_http_methods("GET")
def move_shifts_from_date(request: HttpRequest) -> HttpResponse:
    form = MoveShiftsFromDateForm()
    return render(request, "shifts/move_shifts_from_date.html", {"form": form})


@restrict_to_groups("Office staff", "Supervisors")
@restrict_to_http_methods("GET", "POST")
def move_shifts_from_date_confirmation(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = MoveShiftsFromDateForm(request.POST)
        if not form.is_valid():
            messages.add_message(request, messages.ERROR, f"Form errors: {form.errors}")
            return redirect("move_shifts_from_date")

        from_date: date = form.cleaned_data["from_"]
        to_date: date = form.cleaned_data["to_"]
        from_date_shifts = Shift.objects.all_on_date(from_date)

        return render(
            request,
            "shifts/move_shifts_from_date_confirmation.html",
            {"affected_shifts": from_date_shifts, "from_date": from_date, "to_date": to_date},
        )
    else:  # request.method == "GET"
        from_date = date.fromisoformat(request.GET["from"])
        to_date = date.fromisoformat(request.GET["to"])
        from_date_shifts = Shift.objects.all_on_date(from_date)
        for shift in from_date_shifts:
            start = shift.start.astimezone(pytz.timezone("America/New_York"))
            start = start.replace(
                year=to_date.year,
                month=to_date.month,
                day=to_date.day,
            )
            shift.start = start
            shift.save()

        messages.add_message(
            request, messages.INFO, f"Moved {from_date_shifts.count()} shifts from {from_date} to {to_date}."
        )
        return redirect("move_shifts_from_date")
