import json
import logging

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.shortcuts import get_list_or_404, get_object_or_404, render
from django.urls import reverse

from .forms import EditProfileForm, NewChangeRequestForm
from .models import Shift, ShiftChangeRequest

User = get_user_model()
log = logging.getLogger()


def restrict_to_groups(*groups):
    def decorator(view):
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path())
            if request.user.is_superuser or request.user.groups.filter(name__in=groups).exists():
                return view(request, *args, **kwargs)
            raise PermissionDenied

        return _wrapped_view

    return decorator


@login_required
def index(request):
    pending_shift_change_requests = ShiftChangeRequest.objects.filter(
        target__associated_person=request.user, approved=False
    )
    return render(request, "index.html", {"change_requests": pending_shift_change_requests})


@login_required
def user_profile(request, user_id):
    target_user = get_object_or_404(User, id=user_id)
    target_users_shifts = Shift.objects.filter(associated_person=target_user)
    target_users_shifts = [
        {
            "id": str(shift.id),
            "start": shift.start.isoformat(),
            "end": (shift.start + shift.duration).isoformat(),
            "title": str(shift),
            "allDay": False,
            "url": reverse("view_shift", args=(shift.id,)),
        }
        for shift in target_users_shifts
    ]
    target_users_shifts = json.dumps(target_users_shifts)
    return render(
        request, "users/user_profile.html", {"target_user": target_user, "target_users_shifts": target_users_shifts}
    )


@login_required
def edit_profile(request, user_id):
    if user_id != request.user.id:
        # TODO: let privileged users edit anyone's profile
        raise PermissionDenied
    user = get_object_or_404(User, pk=user_id)
    if request.method == "POST":
        form = EditProfileForm(request.POST)
        if form.is_valid():
            user.first_name = form.cleaned_data["first_name"]
            user.last_name = form.cleaned_data["last_name"]
            user.email = form.cleaned_data["email"]
            user.save()
            return HttpResponseRedirect(reverse("user_profile", args=(user_id,)))
    else:
        form = EditProfileForm(instance=user)
        return render(request, "users/edit_profile.html", {"user_id": user_id, "form": form})


@restrict_to_groups("Office staff", "Supervisors")
def list_users(request, group):
    users = get_list_or_404(User.objects.order_by("last_name"), groups__name=group)
    return render(request, "users/list_users.html", {"users": users, "group": group})


@login_required
def view_shift(request, shift_id):
    shift = get_object_or_404(Shift, pk=shift_id)
    change_requests = ShiftChangeRequest.objects.filter(target=shift)
    return render(request, "shifts/view_shift.html", {"shift": shift, "change_requests": change_requests})


@login_required
def new_shift_change_request(request, shift_id):
    shift = get_object_or_404(Shift, pk=shift_id)
    if shift.associated_person.id != request.user.id:
        # TODO: let privileged users edit anyone's shifts
        raise PermissionDenied
    if request.method == "POST":
        form = NewChangeRequestForm(request.POST)
        if form.is_valid():
            s = ShiftChangeRequest(
                target=shift,
                reason=form.cleaned_data["reason"],
                approved=False,
                approved_by=None,
                approved_on=None,
                new_associated_person=form.cleaned_data["new_associated_person"],
                new_start=form.cleaned_data["new_start"],
                new_duration=form.cleaned_data["new_duration"],
                new_location=form.cleaned_data["new_location"],
            )
            s.save()
            return HttpResponseRedirect(reverse("view_shift", args=(shift_id,)))
    else:
        form = NewChangeRequestForm(
            initial={
                "new_associated_person": shift.associated_person,
                "new_start": shift.start,
                "new_duration": shift.duration,
                "new_location": shift.location,
            }
        )
        return render(request, "shifts/new_shift_change_request.html", {"shift_id": shift_id, "form": form})
