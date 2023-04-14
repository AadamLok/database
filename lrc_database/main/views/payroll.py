from datetime import datetime, timedelta
import pytz
import calendar

from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_list_or_404, get_object_or_404, redirect, render

from ..templatetags.groups import is_privileged
from . import restrict_to_groups, restrict_to_http_methods

from ..models import Shift, Semester, StaffUserPosition
from ..forms import PayrollForm, SemesterSelectForm, UserSelectForm
from ..color_coder import color_coder, get_color_coder_dict

def get_week_from_date(date):
    start_week = date.replace(hour=0, minute=0)
    while start_week.weekday() != 6:
        start_week -= timedelta(days=1)
    end_week = (start_week + timedelta(days=6)).replace(hour=23, minute=59, second=59)
    return start_week, end_week

@login_required
@restrict_to_http_methods("GET", "POST")
def sign_payroll(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        identifier = int([key for key in request.POST.keys() if 'form' in key][0][5:])
        form = PayrollForm(identifier, request.POST)

        if not form.is_valid():
            messages.add_message(request, messages.ERROR, f"Form errors: {form.errors}")
            return redirect("sign_payroll")

        data = form.cleaned_data
        shift_to_edit = Shift.objects.get(id=identifier)
        shift_to_edit.attended = data["attended"]
        shift_to_edit.reason = data["reason"]
        shift_to_edit.signed = True
        week_end = shift_to_edit.start.replace(hour=23, minute=59, second=59, tzinfo=pytz.timezone("America/New_York"))
        while week_end.weekday() != 5:
            week_end += timedelta(days=1)
        late = timezone.now() > week_end
        shift_to_edit.late = late
        if late:
            shift_to_edit.late_datetime = timezone.now()
        shift_to_edit.save()

        if data["attended"] and (shift_to_edit.kind == "SI" or shift_to_edit.kind == "GT"):
            duration = timedelta(hours=2)
            if shift_to_edit.duration > timedelta(hours=1, minutes=15):
                duration += (shift_to_edit.duration-timedelta(hours=1, minutes=15))*(timedelta(hours=1)/timedelta(minutes=45))
            if duration > timedelta(hours=3):
                duration = timedelta(hours=3)
            Shift.objects.create(
                position=shift_to_edit.position,
                start=shift_to_edit.start,
                duration=duration,
                location="None",
                kind="Preparation",
                attended=True,
                signed=True,
                late=shift_to_edit.late,
                late_datetime=shift_to_edit.late_datetime
            )

        return redirect("sign_payroll")
    else:
        context = {"shifts":None}

        now = timezone.now()
        not_signed_shifts = Shift.objects.filter(position__person=request.user, signed = False, start__lte = now).all()
        if not_signed_shifts.count() > 0:
            shifts_info = []
            for shift in not_signed_shifts:
                start = timezone.localtime(shift.start)
                shifts_info.append({
                    'date': start.day,
                    'month': calendar.month_name[start.month],
                    'start': timezone.localtime(start).time,
                    'end': timezone.localtime(start+shift.duration).time,
                    'duration': shift.duration,
                    'kind': shift.kind,
                    'position': f"{shift.location} - {shift.position.position}",
                    'form': PayrollForm(shift.id)
                })
            context["shifts"] = shifts_info

        return render(request, "payroll/sign_payroll.html", context)


def get_user_payroll(user_id, semester):
    context = {"weeks":{}, "color_coder":get_color_coder_dict()}

    shifts = Shift.objects.filter(position__semester=semester, position__person__id=user_id, attended=True, signed=True).all()
    shifts = shifts.order_by("start")
    positions = shifts.values_list('position').distinct()

    if shifts.count() == 0:
        context["total_hours"] = "0.00"
        context["total_pay"] = "$0.00"
    else:
        context["total_hours"] = 0
        context["total_pay"] = 0
        start_week, end_week = get_week_from_date(timezone.localtime(shifts[0].start))
        
        remaining_shifts = shifts.filter(start__gte=start_week)

        while remaining_shifts.count() != 0:
            week_name = f"{start_week.month}/{start_week.day} - {end_week.month}/{end_week.day}"
            position_wise_pay = {str(StaffUserPosition.objects.get(id=key[0])):[[],[],[],[],[],[],[],0,0] for key in positions}
            for shift in remaining_shifts.filter(start__lte=end_week):
                position = str(shift.position)
                hours = round(shift.duration.seconds/3600,2)
                pay = round(shift.duration.seconds/3600 * float(shift.position.hourly_rate),2)
                position_wise_pay[position][(timezone.localtime(shift.start).weekday()+1)%7].append({
                    "time": f"{hours:0.2f}",
                    "id": shift.id,
                    "color": color_coder(shift.kind),
                    "late": shift.late
                })
                position_wise_pay[position][7] += hours
                position_wise_pay[position][8] += pay
                context["total_hours"] += hours
                context["total_pay"] += pay
            for position_pay in position_wise_pay.values():
                position_pay[7] = f"{position_pay[7]:0.2f}"
                position_pay[8] = f"${position_pay[8]:0.2f}"
            context["weeks"][week_name] = position_wise_pay
            start_week += timedelta(days=7)
            end_week += timedelta(days=7)
            remaining_shifts = remaining_shifts.filter(start__gte=start_week)
        context["total_hours"] = f"{context['total_hours']:0.2f}"
        context["total_pay"] = f"${context['total_pay']:0.2f}"
    return context

@login_required
@restrict_to_http_methods("GET")
def view_payroll(request: HttpRequest) -> HttpResponse:
    context = get_user_payroll(request.user.id, Semester.objects.get_active_sem())

    return render(request, "payroll/view_payroll.html", context)

@login_required
@restrict_to_groups("Office staff", "Supervisors")
@restrict_to_http_methods("GET", "POST")
def user_payroll(request: HttpRequest, id: int) -> HttpResponse:
    if request.method =="POST":
        sem = None
        if "semester_select_form" in request.POST:
            form = SemesterSelectForm(request.POST)
            if not form.is_valid():
                messages.add_message(request, messages.ERROR, f"Form errors: {form.errors}")
                return redirect("user_payroll", id)
            data = form.cleaned_data
            sem = data["semester"]
            sem = sem if sem is not None else Semester.objects.get_active_sem()
            context = get_user_payroll(id, sem)
            sem_form = SemesterSelectForm(onchange=True, initial = {'semester': sem })
            context["sem_form"] = sem_form
            user_form = UserSelectForm(onchange=True, initial = {'user': id })
            context["user_form"] = user_form
            context["uid"] = int(id)
            return render(request, "payroll/user_payroll.html", context)
        else:
            form = UserSelectForm(request.POST)
            if not form.is_valid():
                messages.add_message(request, messages.ERROR, f"Form errors: {form.errors}")
                return redirect("user_payroll", id)
            data = form.cleaned_data
            user_id = data["user"].id
            return redirect("user_payroll", user_id)
    else:
        active_sem = Semester.objects.get_active_sem()
        context = get_user_payroll(id, active_sem)
        sem_form = SemesterSelectForm(onchange=True, initial = {'semester': active_sem })
        context["sem_form"] = sem_form
        user_form = UserSelectForm(onchange=True, initial = {'user': id })
        context["user_form"] = user_form
        context["uid"] = int(id)
        return render(request, "payroll/user_payroll.html", context)


@login_required
@restrict_to_groups("Office staff", "Supervisors")
@restrict_to_http_methods("GET", "POST")
def weekly_payroll(request: HttpRequest, offset: int) -> HttpResponse:
    if request.method == "POST":
        pass
    else:
        context = {"offset":offset}
        week_start, week_end = get_week_from_date(timezone.now() - timedelta(days=(7*offset)))
        context["cur_week"] = f"{week_start.month}/{week_start.day} - {week_end.month}/{week_end.day}"

        late_shifts = Shift.objects.filter(
            late=True, 
            attended=True, 
            signed=True, 
            position__semester= Semester.objects.get_active_sem(), 
            late_datetime__gte=week_start, 
            late_datetime__lte=week_end
        ).order_by("start")

        shift_from_this_week = Shift.objects.filter(
            position__semester=Semester.objects.get_active_sem(), 
            start__gte=week_start, 
            start__lte=week_end
        ).order_by("position")

        on_time_shifts = shift_from_this_week.filter(
            attended=True,
            late=False,  
            signed=True
        )

        shifts_not_signed = shift_from_this_week.filter(
            signed=False
        )

        shift_type_with_name = [
            (late_shifts, "late_shifts"),
            (on_time_shifts, "cur_shifts"),
            (shifts_not_signed, "not_signed")
        ]

        for shift_type, shift_type_name in shift_type_with_name:
            info_shifts = {"Total_hours": 0, "Total_pay":0} if shift_type_name != "late_shifts" else {}
            for shift in shift_type:
                info = None
                if shift_type_name == "late_shifts":
                    week_start, week_end = get_week_from_date(shift.start)
                    week_name = f"{week_start.month}/{week_start.day} - {week_end.month}/{week_end.day}"
                    if week_name not in info_shifts:
                        info_shifts[week_name] = {"Total_hours": 0, "Total_pay":0}
                    info = info_shifts[week_name]
                else:
                    info = info_shifts
                person = str(shift.position.person)
                if person not in info:
                    info[person] = {}
                    for pshift in shift_type.filter(position__person=shift.position.person).all():
                        position = pshift.position.str_pos()
                        if position not in info[person]:
                            info[person][position] = [0,0,0,0,0,0,0,0,0]
                    info[person]["Total"] = [0,0,0,0,0,0,0,0,0]
                index = (timezone.localtime(shift.start).weekday()+1)%7
                hours = round(shift.duration.seconds/3600,2)
                pay = round(shift.duration.seconds/3600 * float(shift.position.hourly_rate),2)
                position = shift.position.str_pos()
                
                info[person][position][index] += hours
                info[person][position][7] += hours
                info[person][position][8] += pay

                info[person]["Total"][index] += hours
                info[person]["Total"][7] += hours
                info[person]["Total"][8] += pay

                info["Total_hours"] += hours
                info["Total_pay"] += pay

            context[shift_type_name] = info_shifts

        return render(request, "payroll/weekly_payroll.html", context)