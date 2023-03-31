from typing import List, Union

from django.contrib.auth import views as auth_views
from django.urls import URLPattern, URLResolver, include, path, register_converter
from .converters import DateConverter, NegativeIntConverter

from .views import index
from .views.bulk_shift_editing_views import (
    drop_shifts_on_date,
    drop_shifts_on_date_confirmation,
    move_shifts_from_date,
    move_shifts_from_date_confirmation,
    swap_shift_dates,
    swap_shift_dates_confirmation,
)
from .views.courses import (
    add_course, 
    course_event_feed, 
    edit_course, 
    list_courses, 
    view_course,
    list_course_sections,
    add_course_section,
    edit_course_section,
    add_courses_in_bulk,
    add_sections_in_bulk,
    add_class_detail_in_bulk
)
from .views.hardware import add_hardware, add_loans, edit_hardware, edit_loans, show_hardware, show_loans
from .views.schedule import view_schedule
from .views.shifts import (
    approve_pending_request,
    deny_request,
    make_pending,
    new_drop_request,
    new_shift,
    new_shift_change_request,
    new_shift_request,
    set_to_pending,
    view_drop_shift_requests,
    view_shift,
    view_shift_change_request,
    view_shift_change_requests,
    view_shift_change_requests_by_user,
    view_drop_shift_requests,
    new_shift_recurring,
    view_shift_doc
)
from .views.users import (
    create_user, 
    create_users_in_bulk, 
    edit_profile, list_users, 
    user_event_feed, 
    user_profile, 
    view_or_edit_user, 
    delete_user_staff_position
)
from .views.schedule import view_schedule
from .views.semester import (
    list_semesters, 
    add_semester, 
    edit_semester, 
    delete_holiday, 
    delete_day_switch, 
    change_active_semester
)
from .views.payroll import sign_payroll, view_payroll, user_payroll, weekly_payroll
from .views.pm import pm_schedule, pm_add_meeting
from .views.auth import login_user, reset_password

URLs = List[Union[URLPattern, URLResolver]]

register_converter(DateConverter, 'date')
register_converter(NegativeIntConverter, 'negint')

MISC_URLS: URLs = [
    path("", index, name="index"),
]

ACCOUNTS_URLS: URLs = [
    path("accounts/login/", login_user, name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("accounts/password_change/", auth_views.PasswordChangeView.as_view(), name="password_change"),
    path("accounts/password_change/done/", auth_views.PasswordChangeDoneView.as_view(), name="password_change_done"),
    path("accounts/reset_password/", reset_password, name="reset_password"),
]

API_URLS: URLs = [
    path("api/course_event_feed/<int:course_id>", course_event_feed, name="course_event_feed"),
    path("api/user_event_feed/<int:user_id>", user_event_feed, name="user_event_feed"),
]

COURSES_URLS: URLs = [
    path("courses/", list_courses, name="list_courses"),
    path("courses/<int:course_id>", view_course, name="view_course"),
    path("courses/<int:course_id>/edit", edit_course, name="edit_course"),
    path("courses/add", add_course, name="add_course"),
    path("courses/list_course_sections/<str:sem>", list_course_sections, name="list_course_sections"),
    path("courses/add_course_section", add_course_section, name="add_course_section"),
    path("courses/edit_course_section/<int:course_id>", edit_course_section, name="edit_course_section"),
    path("courses/add_courses_in_bulk", add_courses_in_bulk, name="add_courses_in_bulk"),
    path("courses/add_sections_in_bulk", add_sections_in_bulk, name="add_sections_in_bulk"),
    path("courses/add_class_details_in_bulk", add_class_detail_in_bulk, name="add_class_detail_in_bulk"),
]

HARDWARE_URLS: URLs = [
    path("show_hardware", show_hardware, name="showHardware"),
    path("show_loans", show_loans, name="showLoans"),
    path("edit_loans/<int:loan_id>", edit_loans, name="edit_loans"),
    path("edit_hardware/<int:hardware_id>", edit_hardware, name="edit_hardware"),
    path("add_hardware", add_hardware, name="add_hardware"),
    path("add_loans", add_loans, name="add_loans"),
]

SCHEDULING_URLS: URLs = [
    # fmt: off
    path("scheduling/shift_change_requests/<int:request_id>/set_to_pending", set_to_pending, name="set_to_pending"),
    path("scheduling/bulk/drop_on_date", drop_shifts_on_date, name="drop_shifts_on_date"),
    path("scheduling/bulk/drop_on_date/confirm", drop_shifts_on_date_confirmation, name="drop_shifts_on_date_confirmation"),
    path("scheduling/bulk/swap_shift_dates", swap_shift_dates, name="swap_shift_dates"),
    path("scheduling/bulk/swap_shift_dates/confirmation", swap_shift_dates_confirmation, name="swap_shift_dates_confirmation"),
    path("scheduling/bulk/move_shifts_from_date", move_shifts_from_date, name="move_shifts_from_date"),
    path("scheduling/bulk/move_shifts_from_date/confirm", move_shifts_from_date_confirmation, name="move_shifts_from_date_confirmation"),
    path("scheduling/shift_change_requests/<int:request_id>", view_shift_change_request, name="view_single_request"),
    path("scheduling/shift_change_requests/<int:request_id>/deny", deny_request, name="deny_request"),
    path("scheduling/shift_change_requests/<int:request_id>/make_pending", make_pending, name="make_pending"),
    path("scheduling/shift_change_requests/<int:request_id>/approval_form", approve_pending_request, name="approve_request"),
    path("scheduling/shift_change_requests/<str:kind>/<str:state>", view_shift_change_requests, name="view_shift_change_requests"),
    path("scheduling/drop_shift_requests/<str:kind>/<str:state>", view_drop_shift_requests, name="view_drop_shift_requests"),
    path("scheduling/request_shift", new_shift_request, name="new_shift_request"),
    # fmt: on
]

SHIFTS_URLS: URLs = [
    path("shifts/<int:shift_id>", view_shift, name="view_shift"),
    path("shifts/<int:shift_id>/doc", view_shift_doc, name="view_shift_doc"),
    path("shifts/<int:shift_id>/request_drop", new_drop_request, name="new_drop_request"),
    path("shifts/<int:shift_id>/request_change", new_shift_change_request, name="new_shift_change_request"),
    path("shifts/new", new_shift, name="new_shift"),
    path("shifts/new/recurring", new_shift_recurring, name="new_shift_recurring"),
]

USERS_URLS: URLs = [
    path("users/", list_users, name="list_users"),
    path("users/<int:user_id>", user_profile, name="user_profile"),
    path("users/<int:user_id>/edit", edit_profile, name="edit_profile"),
    path(
        "users/<int:user_id>/shift_change_requests",
        view_shift_change_requests_by_user,
        name="view_shift_change_requests_by_user",
    ),
    path("users/create", create_user, name="create_user"),
    path("users/create/bulk", create_users_in_bulk, name="create_users_in_bulk"),
    path("users/groups/<str:group>", list_users, name="list_users"),
    path("users/view_or_edit/<int:user_id>", view_or_edit_user, name="view_or_edit_user"),
    path("users/delete_staff_position/<int:user_id>/<int:index>", delete_user_staff_position, name="delete_user_staff_position")
]

SCHEDULE_URL: URLs = [path("schedule/<str:kind>/<str:offset>", view_schedule, name="view_schedule")]

SEMESTER_URL: URLs = [
    path("semester/list_semester", list_semesters, name="list_semesters"),
    path("semester/add_semester", add_semester, name="add_semester"),
    path("semester/edit_semester/<str:name>", edit_semester, name="edit_semester"),
    path("semester/delete_holiday/<str:name>/<date:date>", delete_holiday, name="delete_holiday"),
    path("semester/delete_day_switch/<str:name>/<date:date>", delete_day_switch, name="delete_day_switch"), 
    path("semester/change_active_semester/<str:name>", change_active_semester, name="change_active_semester")
]

PAYROLL_URL: URLs = [
    path("payroll/sign", sign_payroll, name="sign_payroll"),
    path("payroll/view", view_payroll, name="view_payroll"),
    path("payroll/user/<int:id>", user_payroll, name="user_payroll"),
    path("payroll/weekly/<negint:offset>", weekly_payroll, name="weekly_payroll"),
]

PM_URL: URLs = [
    path("pm/schedule/<negint:offset>", pm_schedule, name="pm_schedule"),
    path("pm/add-meeting/", pm_add_meeting, name="pm_add_meeting"),
]

urlpatterns: URLs = (
    MISC_URLS + 
    ACCOUNTS_URLS + 
    API_URLS + 
    COURSES_URLS + 
    HARDWARE_URLS + 
    SCHEDULING_URLS + 
    SHIFTS_URLS + 
    USERS_URLS + 
    SCHEDULE_URL + 
    SEMESTER_URL +
    PAYROLL_URL +
    PM_URL
)
