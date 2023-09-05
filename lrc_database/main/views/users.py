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

from ..forms import CreateUserForm, CreateUsersInBulkForm, EditProfileForm, StaffUserPositionForm, EditUserForm
from ..models import LRCDatabaseUser, Semester, Shift, StaffUserPosition, Course, ShiftChangeRequest
from . import personal, restrict_to_groups, restrict_to_http_methods
from ..color_coder import color_coder, get_color_coder_dict

User = get_user_model()


@login_required
@restrict_to_http_methods("GET")
def user_profile(request: HttpRequest, user_id: int) -> HttpResponse:
    target_user = get_object_or_404(User, id=user_id)
    active_positions = StaffUserPosition.objects.filter(person=target_user, semester=Semester.objects.get_active_sem())
    target_users_shifts = json.dumps(
        list(
            map(
                lambda shift: {
                    "id": str(shift.id),
                    "start": shift.start.isoformat(),
                    "end": (shift.start + shift.duration).isoformat(),
                    "title": str(shift),
                    "allDay": False,
                    "url": reverse("view_shift", args=(shift.id,)),
                },
                Shift.objects.filter(position__in=active_positions),
            )
        )
    )

    return render(
        request,
        "users/user_profile.html",
        {"target_user": target_user, "target_users_shifts": target_users_shifts, "color_coder": get_color_coder_dict()},
    )


@login_required
@personal
@restrict_to_http_methods("GET")
def user_event_feed(request: HttpRequest, user_id: int) -> HttpResponse:
    try:
        start = datetime.fromisoformat(request.GET["start"])
        end = datetime.fromisoformat(request.GET["end"])
    except KeyError:
        raise BadRequest("Both start and end dates must be specified.")
    except ValueError:
        raise BadRequest("Either start or end date is not in correct ISO8601 format.")

    user = get_object_or_404(User, id=user_id)
    active_positions = StaffUserPosition.objects.filter(person=user, semester=Semester.objects.get_active_sem())
    shifts = Shift.objects.filter(position__in=active_positions, start__gte=start, start__lte=end)
    shift_change_req = ShiftChangeRequest.objects.filter(new_position__in=active_positions, state__in=["Pending","New"],new_start__gte=start, new_start__lte=end)

    shifts_in_req_ids = list(map(lambda x: x['shift_to_update'],shift_change_req.values('shift_to_update')))
    class_name = {}
    for shift in shifts:
        color = "blue-link"
        if shift.id in shifts_in_req_ids:
            if ShiftChangeRequest.objects.filter(shift_to_update__id=shift.id).order_by('-created').first().state   == "New":
                color = "red-link"
            else:
                color = "green-link"
        class_name[shift.id] = color

    def to_json_shift(shift: Shift) -> Dict[str, Any]:
        return {
            "id": str(shift.id),
            "start": shift.start.isoformat(),
            "end": (shift.start + shift.duration).isoformat(),
            "title": str(shift),
            "allDay": False,
            "url": reverse("view_shift", args=(shift.id,)),
            "color": color_coder(shift.kind),
            "className": class_name[shift.id]
        }
    
    
    def to_json_shift_req(req: ShiftChangeRequest) -> Dict[str, Any]:
        duration = req.new_duration
        if duration is None:
            duration = Shift.objects.get(id=req.shift_to_update.id).duration
        return {
            "id": str(req.id),
            "start": req.new_start.isoformat(),
            "end": (req.new_start + duration).isoformat(),
            "title": f"{req.state} Request - {req.new_kind}",
            "allDay": False,
            "url": reverse("view_single_request", args=(req.id,)),
            "color": color_coder(req.new_kind),
            "textColor": "#f00",
            "className": "red-link" if req.state == "New" else "green-link"
        }

    json_response = list(map(to_json_shift, shifts)) + list(map(to_json_shift_req, shift_change_req))
    return JsonResponse(json_response, safe=False)


@login_required
@restrict_to_http_methods("GET", "POST")
def edit_profile(request: HttpRequest, user_id: int) -> HttpResponse:
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
            return redirect("user_profile", user_id)
        else:
            messages.add_message(request, messages.ERROR, f"Form errors: {form.errors}")
            return redirect("edit_profile", user_id)
    else:
        form = EditProfileForm(instance=user)
        return render(request, "users/edit_profile.html", {"user_id": user_id, "form": form})


@restrict_to_groups("Office staff", "Supervisors")
@restrict_to_http_methods("GET", "POST")
def create_user(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = CreateUserForm(request.POST)
        if form.is_valid():
            user = LRCDatabaseUser.objects.create_user(
                username=form.cleaned_data["email"].lower(),
                email=form.cleaned_data["email"].lower(),
                first_name=form.cleaned_data["first_name"].capitalize(),
                last_name=form.cleaned_data["last_name"].capitalize()
            )
            user.set_unusable_password()
            user.save()
            for group in form.cleaned_data["groups"]:
                group.user_set.add(user)
            messages.add_message(request, messages.SUCCESS, f"Account for {form.cleaned_data['email']} successfully created.")
            return redirect("view_or_edit_user", user.id)
        else:
            messages.add_message(request, messages.ERROR, f"Form errors: {form.errors}")
            return redirect("create_user")
    else:
        form = CreateUserForm()
        return render(request, "users/create_user.html", {"form": form})


@restrict_to_groups("Office staff", "Supervisors")
@restrict_to_http_methods("GET", "POST")
def create_users_in_bulk(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = CreateUsersInBulkForm(request.POST)
        if not form.is_valid():
            messages.add_message(request, messages.ERROR, f"Form errors: {form.errors}")
            return redirect("create_users_in_bulk")
        user_data = form.cleaned_data["user_data"]
        user_data = user_data.split("\n")

        for line_number in range(len(user_data)):
            data = user_data[line_number].split(',')
            data = [s.strip() for s in data]
            if len(data) != 3 or len(data[0]) == 0 or '@' not in data[0] or len(data[1]) == 0 or len(data[2]) == 0:
                messages.add_message(request, messages.ERROR, f"No users have been added yet.\
                                     <br/><br/>Line number <b>{line_number+1}</b>\
                                      doesn't look right.<br/><br/>Please correct this error and try again.")
                return redirect("create_users_in_bulk")
            user_data[line_number] = data

        staff_group = Group.objects.get(name="Staff")
        for line_num, data in enumerate(user_data):
            email, first_name, last_name = data
            try:
                user = LRCDatabaseUser.objects.create_user(
                    username=email.lower(), 
                    email=email.lower(), 
                    first_name=first_name.capitalize(), 
                    last_name=last_name.capitalize()
                )
                user.set_unusable_password()
                user.groups.add(staff_group)
                user.save()
            except Exception as err:
                messages.add_message(request, messages.ERROR, f"Successfully added users till line number\
                                      {line_num}.<br/><br/>Got the following error while trying to add new\
                                      user at line number <b>{line_num+1}</b>:<br/>{err}")
                return redirect("create_users_in_bulk")
        messages.add_message(request, messages.SUCCESS, f"Users successfully created.")
        return redirect("create_users_in_bulk")
    else:
        form = CreateUsersInBulkForm()
        return render(request, "users/create_users_in_bulk.html", {"form": form})


@restrict_to_groups("Office staff", "Supervisors")
@restrict_to_http_methods("GET")
def list_users(request: HttpRequest, group: Optional[str] = None) -> HttpResponse:
    if group is not None:
        if group in ["SI", "Tutor", "GT", "SST", "OursM", "OA"]:
            users = User.objects.filter(groups__name="Staff").all()
            active_sem = Semester.objects.get_active_sem()
            if len(users) > 0:
                user_ids = []
                if group == "SST":
                    SS_course = Course.objects.filter(department="STUDY-SKILL").all()
                    user_ids = StaffUserPosition.objects.filter(Q(person__in=users) & Q(semester=active_sem) & Q(position="Tutor") & Q(tutor_courses__in=SS_course)).all().values('person')
                else:
                    user_ids = StaffUserPosition.objects.filter(Q(person__in=users) & Q(semester=active_sem) & Q(position=group)).all().values('person')
                users = User.objects.filter(id__in=user_ids).all()
        else:
            users = User.objects.filter(groups__name=group).all()
    else:
        group = "All users"
        users = User.objects.all()
    group = "Study Skill Tutor" if group == "SST" else "Group Tutor" if group == "GT" else "OURS Mentor" if group == "OursM" else group
    return render(request, "users/list_users.html", {"users": users, "group": group})


@restrict_to_groups("Office staff", "Supervisors")
def delete_user_staff_position(request: HttpRequest, user_id: int, index: int) -> HttpResponse:
    user = get_object_or_404(User, pk=user_id)
    StaffUserPosition.objects.filter(person=user).all()[index].delete()
    messages.add_message(request, messages.SUCCESS, f"Successfully deleted staff position.")
    return redirect("view_or_edit_user", user_id)

@restrict_to_groups("Office staff", "Supervisors")
@restrict_to_http_methods("GET", "POST")
def view_or_edit_user(request: HttpRequest, user_id: int) -> HttpResponse:
    if request.method == "POST":
        if 'staff_position' in request.POST:
            form = StaffUserPositionForm(request.POST)

            if not form.is_valid():
                messages.add_message(request, messages.ERROR, f"Form errors: {form.errors}")
                return redirect("view_or_edit_user", user_id)

            data = form.cleaned_data
            user = get_object_or_404(User, pk=user_id)

            if data["position"] == "SI" or data["position"] == "GT":
                if data["si_course"] is None:
                    messages.add_message(request, messages.ERROR, f"To add SI/Group-Tutor position, you should assign a SI/Group-Tutor course.")
                    return redirect("view_or_edit_user", user_id)
                elif data["si_course"].semester != data["semester"]:
                    messages.add_message(request, messages.ERROR, f"Trying to add SI/Group-Tutor course from different semester.")
                    return redirect("view_or_edit_user", user_id)
            elif data["position"] == "Tutor" and len(data["tutor_courses"]) == 0:
                messages.add_message(request, messages.ERROR, f"To add Tutor position, you should assign atleast one tutor course.")
                return redirect("view_or_edit_user", user_id)
            elif data["position"] == "PM" and len(data["peers"]) == 0:
                messages.add_message(request, messages.ERROR, f"To add PM position, you should assign atleast one peer.")
                return redirect("view_or_edit_user", user_id)

            new_position = StaffUserPosition.objects.create(
                person=user,
                semester=data["semester"],
                position=data["position"],
                hourly_rate=data["hourly_rate"]
            )

            if data["position"] == "SI":
                new_position.si_course = data["si_course"]
                new_position.save()
                Shift.objects.add_class_shift(new_position, data["si_course"])
            elif data["position"] == "GT":
                new_position.si_course = data["si_course"]
                new_position.save()
            elif data["position"] == "Tutor":
                for course in data["tutor_courses"]:
                    new_position.assign_tutor_course(course)
            elif data["position"] == "PM":
                for peer in data["peers"]:
                    new_position.assign_peer(peer)
            
            messages.add_message(request, messages.SUCCESS, f"Successfully added new staff position to user.")
        else:
            messages.add_message(request, messages.ERROR, f"Function not implemented yet.")
        return redirect("view_or_edit_user", user_id)
    else:
        form_for_position = StaffUserPositionForm()
        user = get_object_or_404(User, pk=user_id)
        form_for_user = EditUserForm(instance=user)
        staff_info = None
        if user.groups.filter(name="Staff").exists():
            staff_info = StaffUserPosition.objects.filter(person=user).all()
        info_to_send = {
            "user_id": user_id, 
            "staff_info": staff_info,
            "form_for_postion": form_for_position,
            "form_for_user": form_for_user,
            "staff": staff_info is not None
        }
        return render(request, "users/view_user.html", info_to_send)