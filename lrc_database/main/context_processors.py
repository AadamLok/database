from typing import TypedDict, Union

from django.db.models import Q
from django.http.request import HttpRequest

from .models import ShiftChangeRequest
from .templatetags.groups import is_privileged


class AlertCountDict(TypedDict):
    pending_si_change_count: int
    pending_tutoring_change_count: int
    pending_si_drop_count: int
    pending_tutoring_drop_count: int
    total_alert_count: int


class EmptyDict(TypedDict):
    pass


def alert_counts(request: HttpRequest) -> Union[AlertCountDict, EmptyDict]:
    """
    Makes counts for various alert types available to all templates as variables, so that we can show alert counts in
    the navbar.
    """

    # If user is not signed in, do no queries.
    if not request.user.is_authenticated:
        return {}

    # If user doesn't have permission to manage shift change requests, do no queries.
    if not is_privileged(request.user):
        return {}

    si_count = ShiftChangeRequest.objects.filter(
        Q(new_kind="SI") | 
        Q(new_position__position="SI") | 
        Q(shift_to_update__position__position="SI"))
    new_si_count_change = si_count.filter(is_drop_request=False, state="New").count()
    pending_si_count_change = si_count.filter(is_drop_request=False, state="Pending").count()
    si_count_drop = si_count.filter(is_drop_request=True, state="New").count()

    gt_count = ShiftChangeRequest.objects.filter(
        Q(new_kind="Group Tutoring") | 
        Q(new_position__position="GT") | 
        Q(shift_to_update__position__position="GT"))
    new_gt_count_change = gt_count.filter(is_drop_request=False, state="New").count()
    pending_gt_count_change = gt_count.filter(is_drop_request=False, state="Pending").count()
    gt_count_drop = gt_count.filter(is_drop_request=True, state="New").count()

    tutoring_count = ShiftChangeRequest.objects.filter(
        (Q(new_kind="Tutoring") | 
         Q(new_position__position="Tutoring") | 
         Q(shift_to_update__position__position="Tutoring")), state="New")
    tutoring_count_change = tutoring_count.filter(is_drop_request=False).count()
    tutoring_count_drop = tutoring_count.filter(is_drop_request=True).count()

    om_count = ShiftChangeRequest.objects.filter(
        (Q(new_kind="OURS Mentor") | 
         Q(new_position__position="OursM") | 
         Q(shift_to_update__position__position="OursM")), state="New")
    om_count_change = om_count.filter(is_drop_request=False).count()
    om_count_drop = om_count.filter(is_drop_request=True).count()

    total_si = new_si_count_change + pending_si_count_change + si_count_drop
    total_gt = new_gt_count_change + pending_gt_count_change + gt_count_drop
    total_tutor = tutoring_count_change + tutoring_count_drop
    total_om = om_count_change + om_count_drop
    total_other = 0

    total = total_si + total_gt + total_tutor + total_om + total_other


    return {
        "total_si": total_si,
        "total_gt": total_gt,
        "total_tutor": total_tutor,
        "total_om": total_om,
        "total_other": total_other,
        "pending_si_change_count": pending_si_count_change,
        "new_si_change_count": new_si_count_change,
        "tutoring_change_count": tutoring_count_change,
        "new_gt_change_count": new_gt_count_change,
        "pending_gt_change_count": pending_gt_count_change,
        "om_change_count": om_count_change,
        "pending_other_change_count": 0,
        "new_other_change_count": 0,
        "si_drop_count": si_count_drop,
        "tutoring_drop_count": tutoring_count_drop,
        "gt_drop_count": gt_count_drop,
        "om_drop_count": om_count_drop,
        "other_drop_count": 0,
        "total_alert_count": total,
    }
