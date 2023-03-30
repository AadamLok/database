from datetime import datetime, timedelta
from typing import Any, Dict

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import BadRequest
from django.db.models import Q
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.timezone import make_aware
import pytz

from ..forms import (
    CourseForm, 
    SemesterSelectForm, 
    FullCourseForm, 
    ReadOnlyFullCourseForm, 
    ClassDetailsForm, 
    AddCoursesInBulkForm, 
    AddCourseSectionsInBulkForm,
    AddClassDetailsInBulkForm
)
from ..models import Course, Shift, Semester, FullCourse, StaffUserPosition, ClassDetails
from . import restrict_to_groups, restrict_to_http_methods

User = get_user_model()


@login_required
@restrict_to_http_methods("GET")
def list_courses(request: HttpRequest) -> HttpResponse:
    courses = Course.objects.order_by("department", "number")
    return render(request, "courses/list_courses.html", {"courses": courses})


@login_required
@restrict_to_http_methods("GET")
def view_course(request: HttpRequest, course_id: int) -> HttpResponse:
    course = get_object_or_404(Course, id=course_id)
    tutors = StaffUserPosition.objects.filter(tutor_courses__in=(course,), semester=Semester.objects.get_active_sem())
    sis = StaffUserPosition.objects.filter(si_course__course=course, semester=Semester.objects.get_active_sem())
    return render(
        request,
        "courses/view_course.html",
        {"course": course, "tutors": tutors, "sis": sis},
    )


@restrict_to_groups("Office staff", "Supervisors")
@restrict_to_http_methods("GET", "POST")
def add_course(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = CourseForm(request.POST)
        if form.is_valid():
            c = Course(**form.cleaned_data)
            c.save()
            return redirect("view_course", c.id)
        else:
            messages.add_message(request, messages.ERROR, f"Form errors: {form.errors}")
            return redirect("add_course")
    else:
        form = CourseForm()
        return render(request, "courses/add_course.html", {"form": form})


@restrict_to_groups("Office staff", "Supervisors")
@restrict_to_http_methods("GET", "POST")
def add_courses_in_bulk(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = AddCoursesInBulkForm(request.POST)
        if form.is_valid():
            course_data = form.cleaned_data["course_data"]
            course_data = course_data.split("\n")

            for line_number in range(len(course_data)):
                data = course_data[line_number].split(',')
                data = [s.strip() for s in data]
                if len(data) != 3 or len(data[0]) == 0 or len(data[1]) == 0 or len(data[2]) == 0:
                    messages.add_message(request, messages.ERROR, f"No course have been added yet.\
                                        <br/><br/>Line number <b>{line_number+1}</b>\
                                        doesn't look right.<br/><br/>Please correct this error and try again.")
                    return redirect("add_courses_in_bulk")
                course_data[line_number] = data

            for line_num, data in enumerate(course_data):
                department, number, name = data
                try:
                    Course.objects.create(
                        department=department.upper(),
                        number=number.upper(),
                        name=name
                    )
                except Exception as err:
                    messages.add_message(request, messages.ERROR, f"Successfully added courses till line number\
                                        {line_num}.<br/><br/>Got the following error while trying to add new\
                                        course at line number <b>{line_num+1}</b>:<br/>{err}")
                    return redirect("add_course_in_bulk")
            messages.add_message(request, messages.SUCCESS, f"Courses successfully created.")
            return redirect("add_courses_in_bulk")
        else:
            messages.add_message(request, messages.ERROR, f"Form errors: {form.errors}")
            return redirect("add_courses_in_bulk")
    else:
        form = AddCoursesInBulkForm()
        return render(request, "courses/add_courses_in_bulk.html", {"form": form})


@restrict_to_groups("Office staff", "Supervisors")
@restrict_to_http_methods("GET", "POST")
def list_course_sections(request: HttpRequest, sem:str) -> HttpResponse:
    if request.method == "POST":
        form = SemesterSelectForm(request.POST)
        
        if not form.is_valid():
            messages.add_message(request, messages.ERROR, f"Form errors: {form.errors}")
            return redirect("list_course_sections", sem)

        data = form.cleaned_data

        return redirect("list_course_sections", data["semester"].name)
    else:
        filter_sem = Semester.objects.filter(name=sem).first() if sem != "none" else Semester.objects.get_active_sem()
        form = SemesterSelectForm(initial={'semester':filter_sem})
        form.fields['semester'].widget.attrs.update({"onchange" : "post_form()"})
        courses = FullCourse.objects.filter(semester=filter_sem).all()
        context = {"form": form, "sem": sem, "courses": courses}
        return render(request, "courses/list_course_sections.html", context)

@restrict_to_groups("Office staff", "Supervisors")
@restrict_to_http_methods("GET", "POST")
def add_course_section(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = FullCourseForm(request.POST)
        
        if not form.is_valid():
            messages.add_message(request, messages.ERROR, f"Form errors: {form.errors}")
            return redirect("add_course_section")
        
        data = form.cleaned_data

        course = FullCourse.objects.create(
			semester=data["semester"],
			course=data["course"],
			faculty=data["faculty"]
		)

        return redirect("edit_course_section", course.id)
    else:
        form = FullCourseForm()
        context = {"form": form}
        return render(request, "courses/add_course_section.html", context)

@restrict_to_groups("Office staff", "Supervisors")
@restrict_to_http_methods("GET","POST")
def edit_course_section(request: HttpRequest, course_id: int) -> HttpResponse:
    if request.method == "POST":
        form = ClassDetailsForm(request.POST)
        
        if not form.is_valid():
            messages.add_message(request, messages.ERROR, f"Form errors: {form.errors}")
            return redirect("edit_course_section", course_id)
        
        data = form.cleaned_data

        ClassDetails.objects.create(
            full_course=FullCourse.objects.get(id=course_id),
            location=data["location"],
            class_day=data["class_day"],
            class_time=data["class_time"],
            class_duration=data["class_duration"]
        )

        return redirect("edit_course_section", course_id)
    else:
        context = {"course_id": course_id}
        context["course_form"] = ReadOnlyFullCourseForm(instance=FullCourse.objects.get(id=course_id))
        context["class_form"] = ClassDetailsForm()
        context["class_times"] = ClassDetails.objects.filter(full_course__id=course_id).all()

        return render(request, "courses/edit_course_section.html", context)

@restrict_to_groups("Office staff", "Supervisors")
@restrict_to_http_methods("GET")
def delete_class_time(request: HttpRequest, class_id: int, course_id: int) -> HttpResponse:
    ClassDetails.objects.get(id=class_id).delete()
    return redirect("edit_course_section", course_id)

@restrict_to_groups("Office staff", "Supervisors")
@restrict_to_http_methods("GET", "POST")
def edit_course(request: HttpRequest, course_id: int) -> HttpResponse:
    course = get_object_or_404(Course, pk=course_id)
    if request.method == "POST":
        form = CourseForm(request.POST)
        if form.is_valid():
            course.department = form.cleaned_data["department"].upper()
            course.number = form.cleaned_data["number"].upper()
            course.name = form.cleaned_data["name"]
            course.save()
            return redirect("view_course", course.id)
        else:
            messages.add_message(request, messages.ERROR, f"Form errors: {form.errors}")
            return redirect("edit_course", course_id)
    else:
        form = CourseForm(
            initial={
                "department": course.department,
                "number": course.number,
                "name": course.name,
            }
        )
        return render(request, "courses/edit_course.html", {"form": form, "course_id": course.id})


@login_required
@restrict_to_http_methods("GET")
def course_event_feed(request: HttpRequest, course_id: int) -> JsonResponse:
    try:
        start = datetime.fromisoformat(request.GET["start"])
        end = datetime.fromisoformat(request.GET["end"])
    except KeyError:
        raise BadRequest("Both start and end dates must be specified.")
    except ValueError:
        raise BadRequest("Either start or end date is not in correct ISO8601 format.")

    course = get_object_or_404(Course, id=course_id)

    # TODO: problematic, see comment on user_event_feed
    shifts = Shift.objects.filter(
        Q(position__si_course__course=course) | Q(position__tutor_courses__in=(course,)),
        start__gte=start,
        start__lte=end,
    )

    def to_json(shift: Shift) -> Dict[str, Any]:
        color = "black"
        if shift.kind == "SI":
            color = "orange"
        elif shift.kind == "Tutoring":
            color = "green"
        elif shift.kind == "Training":
            color = "red"
        elif shift.kind == "Observation":
            color = "blue"
        elif shift.kind == "Class":
            color = "magenta"
        elif shift.kind == "SI-Preparation":
            color = "teal"
        return {
            "id": str(shift.id),
            "start": shift.start.isoformat(),
            "end": (shift.start + shift.duration).isoformat(),
            "title": str(shift),
            "allDay": False,
            "url": reverse("view_shift", args=(shift.id,)),
            "color": color,
        }

    json_response = list(map(to_json, shifts))
    return JsonResponse(json_response, safe=False)


@restrict_to_groups("Office staff", "Supervisors")
@restrict_to_http_methods("GET", "POST")
def add_sections_in_bulk(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = AddCourseSectionsInBulkForm(request.POST)
        if form.is_valid():
            course_data = form.cleaned_data["course_data"]
            course_data = course_data.split("\n")

            for line_number in range(len(course_data)):
                data = course_data[line_number].split(',')
                data = [s.strip() for s in data]
                if len(data) != 3 or len(data[0]) == 0 or len(data[1]) == 0 or len(data[2]) == 0:
                    messages.add_message(request, messages.ERROR, f"No course have been added yet.\
                                        <br/><br/>Line number <b>{line_number+1}</b>\
                                        doesn't look right.<br/><br/>Please correct this error and try again.")
                    return redirect("add_sections_in_bulk")
                course_data[line_number] = data

            active_sem = Semester.objects.get_active_sem()

            for line_num, data in enumerate(course_data):
                department, number, faculty = data
                try:
                    course = Course.objects.get(
                        department=department.upper(), 
                        number=number.upper()
                    )
                    FullCourse.objects.create(
                        semester=active_sem,
                        course=course,
                        faculty=faculty
                    )
                except Exception as err:
                    messages.add_message(request, messages.ERROR, f"Successfully added courses till line number\
                                        {line_num}.<br/><br/>Got the following error while trying to add new\
                                        course at line number <b>{line_num+1}</b>:<br/>{err}")
                    return redirect("add_sections_in_bulk")
            messages.add_message(request, messages.SUCCESS, f"Courses successfully created.")
            return redirect("add_sections_in_bulk")
        else:
            messages.add_message(request, messages.ERROR, f"Form errors: {form.errors}")
            return redirect("add_sections_in_bulk")
    else:
        form = AddCourseSectionsInBulkForm()
        return render(request, "courses/add_sections_in_bulk.html", {"form": form})

@restrict_to_groups("Office staff", "Supervisors")
@restrict_to_http_methods("GET", "POST")
def add_class_detail_in_bulk(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = AddClassDetailsInBulkForm(request.POST)
        if form.is_valid():
            class_data = form.cleaned_data["class_data"]
            class_data = class_data.split("\n")

            for line_number in range(len(class_data)):
                data = class_data[line_number].split(',')
                data = [s.strip() for s in data]
                if len(data) != 5 or len(data[0]) == 0 or len(data[1]) == 0 or len(data[2]) == 0 or len(data[3]) == 0 or len(data[4]) == 0:
                    messages.add_message(request, messages.ERROR, f"No course have been added yet.\
                                        <br/><br/>Line number <b>{line_number+1}</b>\
                                        doesn't look right.<br/><br/>Please correct this error and try again.")
                    return redirect("add_class_detail_in_bulk")
                class_data[line_number] = data

            timezone= pytz.timezone("America/New_York")

            for line_num, data in enumerate(class_data):
                full_course_id, class_day, class_time, class_location, class_duration = data
                try:
                    class_day = datetime.strptime(class_day, "%A").weekday()
                    class_time = make_aware(datetime.strptime(class_time,"%H:%M"), timezone=timezone).time()
                    class_duration =  class_duration.split(":")
                    class_duration = timedelta(hours=int(class_duration[0]), minutes=int(class_duration[1]))
                    ClassDetails.objects.create(
                        full_course = FullCourse.objects.get(id=full_course_id),
                        location = class_location,
                        class_day = class_day,
                        class_time = class_time,
                        class_duration = class_duration
                    )
                except Exception as err:
                    messages.add_message(request, messages.ERROR, f"Successfully added courses till line number\
                                        {line_num}.<br/><br/>Got the following error while trying to add new\
                                        course at line number <b>{line_num+1}</b>:<br/>{err}")
                    return redirect("add_class_detail_in_bulk")
            messages.add_message(request, messages.SUCCESS, f"Courses successfully created.")
            return redirect("add_class_detail_in_bulk")
        else:
            messages.add_message(request, messages.ERROR, f"Form errors: {form.errors}")
            return redirect("add_class_detail_in_bulk")
    else:
        form = AddClassDetailsInBulkForm()
        return render(request, "courses/add_class_details_in_bulk.html", {"form": form})