from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from . import restrict_to_groups, restrict_to_http_methods
from ..email.mail_service import send_email 


@login_required
@restrict_to_http_methods("GET", "POST")
@restrict_to_groups("Office staff", "Supervisors")
def test_something(request):
    send_email()
    return redirect("index")
    # return render(
    #     request,
    #     "email/test.html",
    #     {
    #         "name": "Aadam",
    #         "reason": "Exam Review 1",
    #         "date": "Dec 1, 2023",
    #         "time": "10:00 - 12:00 AM",
    #         "location": "ILC S211",
	# 	}
    # )