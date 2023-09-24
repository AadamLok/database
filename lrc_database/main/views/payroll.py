from datetime import datetime, timedelta
import pytz
import calendar
import json

from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_list_or_404, get_object_or_404, redirect, render

from ..templatetags.groups import is_privileged
from . import restrict_to_groups, restrict_to_http_methods

from ..models import Shift, Semester, StaffUserPosition, PunchedIn, PayrollCheck
from ..forms import PayrollForm, SemesterSelectForm, UserSelectForm, DateSelectForm
from ..color_coder import color_coder, get_color_coder_dict

def get_week_from_date(date):
    start_week = date.replace(hour=0, minute=0)
    while start_week.weekday() != 6:
        start_week -= timedelta(days=1)
    end_week = (start_week + timedelta(days=6)).replace(hour=23, minute=59, second=59)
    return start_week, end_week

def get_week_date(date):
    start_week = date
    while start_week.weekday() != 5:
        start_week -= timedelta(days=1)
    if isinstance(start_week, datetime):
        start_week = start_week.date()
    return start_week

@login_required
@restrict_to_http_methods("GET", "POST")
def sign_payroll(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        data = None
        
        try:
            data = json.loads(request.body)
        except:
            data = None

        if data is not None:
            if data['type'] == 'in':
                PunchedIn.objects.create(
                    position=StaffUserPosition.objects.get(
                        position=data['shift'],
                        semester=Semester.objects.get_active_sem(),
                        person=request.user
                    ),
                    start=timezone.localtime()
                )
            elif data['type'] == 'undo':
                PunchedIn.objects.get(
                    position=StaffUserPosition.objects.get(
                        position=data['shift'],
                        semester=Semester.objects.get_active_sem(),
                        person=request.user
                    )
                ).delete()
            else:
                punched_in = PunchedIn.objects.get(
                    position=StaffUserPosition.objects.get(
                        position=data['shift'],
                        semester=Semester.objects.get_active_sem(),
                        person=request.user
                    )
                )
                Shift.objects.create(
                    position = StaffUserPosition.objects.get(
                        position=data['shift'],
                        semester=Semester.objects.get_active_sem(),
                        person=request.user
                    ),
                    start = punched_in.start,
                    duration =  timezone.localtime() - punched_in.start,
                    location = "Library",
                    kind = "OURS Mentor" if data['shift'] == "OursM" else "OA Hours",
                )
                punched_in.delete()
            return redirect("sign_payroll")
        attended_ids = []
        for key in sorted(request.POST.keys()):
            if key == "csrfmiddlewaretoken":
                continue
            attended, shift_id = key.split('-')
            attended = attended == "att"
            shift_id = int(shift_id)

            if attended:
                attended_ids.append(shift_id)
            elif shift_id in attended_ids:
                continue

            shift_to_edit = Shift.objects.get(id=shift_id)
            shift_to_edit.attended = attended
            shift_to_edit.reason = "" if attended else request.POST[key]
            shift_to_edit.signed = True
            week_end = shift_to_edit.start.replace(hour=23, minute=59, second=59, tzinfo=pytz.timezone("America/New_York"))
            while week_end.weekday() != 5:
                week_end += timedelta(days=1)
            
            PayrollCheck.objects.add_person_if_not_exists(request.user, get_week_date(shift_to_edit.start))
            payroll_check = PayrollCheck.objects.get(person=request.user, week_start=get_week_date(shift_to_edit.start))
            shift_day_index = (shift_to_edit.start.weekday() - 5) % 7
            make_not_approved = False
            if payroll_check.approved:
                make_not_approved = True
                payroll_check.additional_pay_details[str(shift_to_edit.position.hourly_rate)][shift_day_index] += round(shift_to_edit.duration.seconds/3600, 2)
            else:
                payroll_check.pay_details[str(shift_to_edit.position.hourly_rate)][shift_day_index] += round(shift_to_edit.duration.seconds/3600, 2)
            
            late = timezone.localtime() > week_end
            shift_to_edit.late = late
            if late:
                shift_to_edit.late_datetime = timezone.localtime()
            shift_to_edit.save()
            if attended and (shift_to_edit.kind == "SI" or shift_to_edit.kind == "Group Tutoring"):
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
                if payroll_check.approved:
                    make_not_approved = True
                    payroll_check.additional_pay_details[str(shift_to_edit.position.hourly_rate)][shift_day_index] += round(duration.seconds/3600, 2)
                else:
                    payroll_check.pay_details[str(shift_to_edit.position.hourly_rate)][shift_day_index] += round(duration.seconds/3600, 2)
            
            if  make_not_approved:
                payroll_check.approved = False
            payroll_check.save()

        return redirect("sign_payroll")
    
    else:
        context = {"shifts":None}

        now = timezone.localtime()
        not_signed_shifts = Shift.objects.filter(position__semester=Semester.objects.get_active_sem(), position__person=request.user, signed = False, start__lte = now).all()
        if not_signed_shifts.count() > 0:
            shifts_info = []
            for shift in not_signed_shifts:
                start = timezone.localtime(shift.start)
                shifts_info.append({
                    'date': start.day,
                    'month': calendar.month_name[start.month],
                    'start': start.time,
                    'end': (start+shift.duration).time,
                    'duration': shift.duration,
                    'kind': shift.kind,
                    'position': f"{shift.location} - {shift.position.position}",
                    'id': shift.id,
                    'name': f"{str(shift)}, {start.month}/{start.day}"
                })
            context["shifts"] = shifts_info

        context['OURSMentor'] = request.user.is_ours_mentor()
        if context['OURSMentor']:
            context['OURS_clocked_in'] = PunchedIn.objects.filter(
                position=StaffUserPosition.objects.get(
                    position='OursM',
                    semester=Semester.objects.get_active_sem(),
                    person=request.user
                )
            ).exists()
        
        context['OA'] = request.user.is_oa()
        if context['OA']:
            context['OA_clocked_in'] = PunchedIn.objects.filter(
                position=StaffUserPosition.objects.get(
                    position='OA',
                    semester=Semester.objects.get_active_sem(),
                    person=request.user
                )
            ).exists()

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
        week_start, week_end = get_week_from_date(timezone.localtime() - timedelta(days=(7*offset)))
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
                person = shift.position.person.str_last_name_first()
                if person not in info:
                    info[person] = {}
                    old_pay_rate = -1
                    pay_rate = -1
                    for pshift in shift_type.filter(position__person=shift.position.person).order_by("position__hourly_rate").all():
                        position = pshift.position.str_pos()
                        pay_rate = round(pshift.position.hourly_rate,2)
                        if position not in info[person]:
                            info[person][position] = [0,0,0,0,0,0,0,0,0]
                        if pay_rate != old_pay_rate:
                            info[person][f"Total@{pay_rate}"] = [0,0,0,0,0,0,0,0,0]
                        if old_pay_rate == -1:
                            old_pay_rate = pay_rate
                    info[person][f"Total@{pay_rate}"] = [0,0,0,0,0,0,0,0,0]
                    info[person]["Total"] = [0,0,0,0,0,0,0,0,0]
                index = (timezone.localtime(shift.start).weekday()+1)%7
                hours = round(shift.duration.seconds/3600,2)
                pay_rate = round(shift.position.hourly_rate, 2)
                pay = round(shift.duration.seconds/3600 * float(shift.position.hourly_rate),2)
                position = shift.position.str_pos()
                
                info[person][position][index] += hours
                info[person][position][7] += hours
                info[person][position][8] += pay

                pay_key = f"Total@{pay_rate}"
                info[person][pay_key][index] += hours
                info[person][pay_key][7] += hours
                info[person][pay_key][8] += pay

                info[person]["Total"][index] += hours
                info[person]["Total"][7] += hours
                info[person]["Total"][8] += pay

                info["Total_hours"] += hours
                info["Total_pay"] += pay
            context[shift_type_name] = dict(sorted(info_shifts.items()))

        return render(request, "payroll/weekly_payroll.html", context)

@login_required
@restrict_to_groups("Office staff", "Supervisors")
@restrict_to_http_methods("GET", "POST")
def user_new_weekly_payroll(request, user_id, date):
    display_payroll = PayrollCheck.objects.get(person__id=user_id, week_start=get_week_date(date))
    
    if request.method == "POST":
        approved = False
        try:
            approved = request.POST['approved'] == "on"
            new_pay_details = {}
            new_additional_pay = {}
            for pay in display_payroll.pay_details:
                new_pay_details[pay] = [sum(x) for x in zip(display_payroll.pay_details[pay], display_payroll.additional_pay_details[pay])]
                new_additional_pay[pay] = [0,0,0,0,0,0,0]
            display_payroll.pay_details = new_pay_details
            display_payroll.additional_pay_details = new_additional_pay
        except:
            approved = False
        display_payroll.approved = approved
        display_payroll.save()
    
    info = {}
    for key in display_payroll.pay_details.keys():
        final = [0,0,0,0,0,0,0]
        for i in range(7):
            reg = display_payroll.pay_details[key][i]
            extra = display_payroll.additional_pay_details[key][i]
            total = reg + extra
            final[i] = f'{reg:0.2f}'
            if extra != 0:
                final[i] += f'<b> + {extra:0.2f} = {total:0.2f}</b>'
        info[key] = final
    
    
    return render(
        request,
        "payroll/user_new_weekly_payroll.html",
        {"payroll": display_payroll, "date": date, "info":info},
    )

@login_required
@restrict_to_groups("Office staff", "Supervisors")
@restrict_to_http_methods("GET", "POST")
def new_weekly_payroll(request, date):
    if request.method == "POST":
        form = DateSelectForm(request.POST)
        if not form.is_valid():
            messages.add_message(request, messages.ERROR, f"Form errors: {form.errors}")
            return redirect("new_weekly_payroll", date)
        return redirect("new_weekly_payroll", form.cleaned_data["date"])
    else:
        form = DateSelectForm(initial={
            "date": date,
        })
        
        week_start_date = get_week_date(date)
        display_payroll = PayrollCheck.objects.filter(week_start=week_start_date).all()
        
        return render(
            request,
            "payroll/new_weekly_payroll.html",
            {"form": form, "display_payroll": display_payroll, "date": week_start_date},
        )