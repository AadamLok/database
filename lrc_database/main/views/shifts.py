from datetime import datetime, timedelta
from this import d
from typing import Optional

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_list_or_404, get_object_or_404, redirect, render
from django.urls import reverse
from django.contrib.auth import get_user_model

from ..forms import (
    ApproveChangeRequestForm,
    NewChangeRequestForm,
    NewDropRequestForm,
    NewShiftForm,
    NewShiftForTutorForm,
    NewShiftRecurringForm
)
from ..models import Shift, ShiftChangeRequest
from ..templatetags.groups import is_privileged
from . import restrict_to_groups, restrict_to_http_methods

User = get_user_model()


@login_required
@restrict_to_http_methods("GET")
def view_shift(request: HttpRequest, shift_id: int) -> HttpResponse:
    shift = get_object_or_404(Shift, pk=shift_id)
    change_requests = ShiftChangeRequest.objects.filter(shift_to_update=shift)
    return render(
        request,
        "shifts/view_shift.html",
        {"shift": shift, "change_requests": change_requests},
    )


@login_required
@restrict_to_http_methods("GET", "POST")
def new_shift_change_request(request: HttpRequest, shift_id: int) -> HttpResponse:
    shift = get_object_or_404(Shift, pk=shift_id)
    if shift.associated_person.id != request.user.id:
        # TODO: let privileged users edit anyone's shifts
        raise PermissionDenied
    if request.method == "POST":
        form = NewChangeRequestForm(request.POST)
        if form.is_valid():
            s = ShiftChangeRequest(
                shift_to_update=shift,
                state="New",
                new_associated_person=request.user,
                # approved_by=None,
                # approved_on=None,
                **form.cleaned_data,
            )
            s.save()
            return redirect("view_shift", shift_id)
        else:
            messages.add_message(request, messages.ERROR, f"Form errors: {form.errors}")
            return redirect("new_shift_change_request", shift_id)
    else:
        form = NewChangeRequestForm(
            initial={
                "new_start": shift.start,
                "new_duration": shift.duration,
                "new_location": shift.location,
                "new_kind": shift.kind,
            }
        )
        return render(
            request,
            "shifts/new_shift_change_request.html",
            {"shift_id": shift_id, "form": form},
        )


# View all NEW requests
@restrict_to_groups("Office staff", "Supervisors")
@restrict_to_http_methods("GET")
def view_shift_change_requests(request: HttpRequest, kind: str, state: str) -> HttpResponse:
    if kind == "All":
        requests = ShiftChangeRequest.objects.filter(state=state)
    else:
        requests = ShiftChangeRequest.objects.filter((Q(new_kind=kind) | Q(shift_to_update__kind=kind)), state=state, is_drop_request=False)
    return render(
        request,
        "scheduling/view_shift_change_requests.html",
        {"change_requests": requests, "kind": kind, "state": state, "drop": False},
    )

@restrict_to_groups("Office staff", "Supervisors")
@restrict_to_http_methods("GET")
def view_drop_shift_requests(request: HttpRequest, kind: str, state: str) -> HttpResponse:
    requests = ShiftChangeRequest.objects.filter((Q(new_kind=kind) | Q(shift_to_update__kind=kind)), state=state, is_drop_request=True)
    return render(
        request,
        "scheduling/view_shift_change_requests.html",
        {"change_requests": requests, "kind": kind, "state": state, "drop": True},
    )


@login_required
@restrict_to_http_methods("GET")
def view_shift_change_requests_by_user(request: HttpRequest, user_id: int) -> HttpResponse:
    if not is_privileged(request.user) and request.user.id != user_id:
        raise PermissionDenied
    requests = ShiftChangeRequest.objects.filter(
        (Q(new_associated_person__id=user_id) | Q(shift_to_update__associated_person__id=user_id)),
    )
    target_user = get_object_or_404(User, id=user_id)
    return render(
        request,
        "scheduling/view_shift_change_requests.html",
        {"change_requests": requests, "kind": f"{target_user.first_name}'s"},
    )

@login_required
@restrict_to_http_methods("GET")
def view_shift_change_request(request: HttpRequest, request_id: int) -> HttpResponse:
    shift_request = get_object_or_404(ShiftChangeRequest, pk=request_id)
    is_for_user = False
    if shift_request.new_associated_person == request.user:
        is_for_user = True
    elif shift_request.shift_to_update is not None and shift_request.shift_to_update.associated_person == request.user:
        is_for_user = True
    if not is_privileged(request.user) and not is_for_user:
        raise PermissionDenied
    return render(request, "shifts/view_request.html", {"shift_request": shift_request})


@restrict_to_groups("Office staff", "Supervisors")
@restrict_to_http_methods("GET")
def deny_request(request: HttpRequest, request_id: int) -> HttpResponse:
    shift_request = get_object_or_404(ShiftChangeRequest, id=request_id)
    shift_request.state = "Not Approved"
    shift_request.save()
    return redirect("view_single_request", request_id)


@restrict_to_groups("Office staff", "Supervisors")
@restrict_to_http_methods("GET", "POST")
def approve_pending_request(request: HttpRequest, request_id: int) -> HttpResponse:
    request_cur = get_object_or_404(ShiftChangeRequest, id=request_id)
    shift = request_cur.shift_to_update or Shift()

    if request_cur.is_drop_request:
        request_cur.shift_to_update.delete()
        messages.add_message(request, messages.INFO, "Shift dropped.")
        return redirect("index")

    initial = {
        "associated_person": request_cur.new_associated_person or shift.associated_person,
        "start": request_cur.new_start or shift.start,
        "duration": request_cur.new_duration or shift.duration,
        "location": request_cur.new_location or shift.location,
        "kind": request_cur.new_kind or shift.kind,
    }

    if request.method == "POST":
        form = ApproveChangeRequestForm(
            request.POST,
            instance=shift,
            initial=initial,
        )

        if not form.is_valid():
            messages.add_message(request, messages.ERROR, f"Form errors: {form.errors}")
            return redirect("view_single_request", request_id)

        form.save()
        request_cur.state = "Approved"
        request_cur.save()
        return redirect("index")

    else:
        form = ApproveChangeRequestForm(instance=shift, initial=initial)
        return render(request, "scheduling/approvePendingForm.html", {"form": form, "request_id": request_id})


@restrict_to_groups("Office staff", "Supervisors")
@restrict_to_http_methods("GET", "POST")
def new_shift(request: HttpRequest) -> HttpResponse:
    if request.method == "GET":
        form = NewShiftForm()
        return render(request, "shifts/new_shift.html", {"form": form})
    else:
        form = NewShiftForm(request.POST)
        if form.is_valid():
            shift = Shift(**form.cleaned_data)
            shift.save()
            return redirect("view_shift", shift.id)
        else:
            messages.add_message(request, messages.ERROR, f"Form errors: {form.errors}")
            return redirect("new_shift")


@restrict_to_groups("Office staff", "Supervisors")
@restrict_to_http_methods("GET", "POST")
def new_shift_recurring(request: HttpRequest) -> HttpResponse:
    if request.method == "GET":
        form = NewShiftRecurringForm()
        return render(request, "shifts/new_shift_recurring.html", {"form": form})
    else:
        form = NewShiftRecurringForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            rec_start_date = data["recurring_start_date"]
            rec_end_date = data["recurring_end_date"]
            rec_day_of_week = int(data["recurring_day_of_week"])
            diff = (rec_day_of_week - rec_start_date.weekday()) % 7
            shift_time = data["shift_start_time"]
            first_shift_date = rec_start_date + timedelta(days=diff)
            first_shift = datetime.combine(first_shift_date, shift_time)

            shift_data = {
                'associated_person': data["associated_person"], 
                'duration': data["duration"], 
                'location': data["location"], 
                'kind': data["kind"],
                'start': None
            }

            shift_start = first_shift

            while shift_start.date() <= rec_end_date:
                shift_data["start"] = shift_start
                final_shift = Shift(**shift_data)
                final_shift.save()
                shift_start += timedelta(days=7)

            first_name = data["associated_person"].first_name
            messages.add_message(request, messages.SUCCESS, f"Succesfully added recuring shift for {first_name}.")
            return redirect("new_shift_recurring")
        else:
            messages.add_message(request, messages.ERROR, f"Form errors: {form.errors}")
            return redirect("new_shift_recurring")

@restrict_to_groups("Tutors")
@restrict_to_http_methods("GET", "POST")
def new_shift_tutors_only(request: HttpRequest) -> HttpResponse:
    if request.method == "GET":
        form = NewShiftForTutorForm()
        return render(
            request,
            "shifts/new_shift_request_tutors.html",
            {"form": form, "form_action_url": reverse("new_shift_tutors_only"), "form_title": "Create new shift"},
        )
    else:
        form = NewShiftForTutorForm(request.POST)
        if form.is_valid():
            shift = Shift(associated_person=request.user, location="LRC", kind="Tutoring", **form.cleaned_data)
            shift.save()
            return redirect("view_shift", shift.id)
        else:
            messages.add_message(request, messages.ERROR, f"Form errors: {form.errors}")
            return redirect("new_shift_tutors_only")


@restrict_to_groups("SIs")
@restrict_to_http_methods("GET", "POST")
def new_shift_request(request: HttpRequest) -> HttpResponse:
    if request.method == "GET":
        form = NewChangeRequestForm()
        return render(
            request,
            "shifts/new_shift_request.html",
            {"form": form},
        )
    else:
        form = NewChangeRequestForm(request.POST)
        print(form.data)
        if form.is_valid():
            change_request = ShiftChangeRequest(
                shift_to_update=None,
                state="New",
                new_associated_person=request.user,
                # approved_by=None,
                # approved_on=None,
                **form.cleaned_data,
            )
            change_request.save()
            return redirect("view_single_request", change_request.id)
        else:
            messages.add_message(request, messages.ERROR, f"Form errors: {form.errors}")
            return redirect("new_shift_request")


@restrict_to_groups("SIs", "Tutors")
@restrict_to_http_methods("GET", "POST")
def new_drop_request(request: HttpRequest, shift_id: int) -> HttpResponse:
    shift = get_object_or_404(Shift, id=shift_id)
    if shift.associated_person != request.user:
        raise PermissionDenied

    if request.method == "GET":
        form = NewDropRequestForm()
        return render(
            request,
            "shifts/new_drop_request.html",
            {"form": form, "shift_id": shift_id},
        )
    else:
        form = NewDropRequestForm(request.POST)
        if form.is_valid():
            change_request = ShiftChangeRequest(
                shift_to_update=shift,
                state="New",
                is_drop_request=True,
                new_associated_person=request.user,
                new_kind=shift.kind,
                new_start=shift.start,
                # approved_by=None,
                # approved_on=None,
                **form.cleaned_data,
            )
            change_request.save()
            return redirect("view_single_request", change_request.id)
        else:
            messages.add_message(request, messages.ERROR, f"Form errors: {form.errors}")
            return redirect("new_shift_request")
