from datetime import datetime
from typing import Any, Dict

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import BadRequest
from django.db.models import Q
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from ..forms import CourseForm, SemesterSelectForm, FullCourseForm, ReadOnlyFullCourseForm, ClassDetailsForm
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
            course.department = form.cleaned_data["department"]
            course.number = form.cleaned_data["number"]
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
        return {
            "id": str(shift.id),
            "start": shift.start.isoformat(),
            "end": (shift.start + shift.duration).isoformat(),
            "title": str(shift),
            "allDay": False,
            "url": reverse("view_shift", args=(shift.id,)),
        }

    json_response = list(map(to_json, shifts))
    return JsonResponse(json_response, safe=False)
