from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse

from . import restrict_to_groups, restrict_to_http_methods
from ..email.mail_service import send_email 


@login_required
@restrict_to_http_methods("GET", "POST")
@restrict_to_groups("Office staff", "Supervisors")
def test_something(request):
    # send_email()
    # return redirect("index")
    return render(
        request,
        "email/shift_request.html",
        {
			'name': 'Aadam',
			'reason': 'Exam Review',
			'has_old_shift': True,
            'has_new_shift': True,
			'drop_req': False,
			'url': f"https://lrcstaff.umass.edu{reverse('view_single_request',args=[100])}",
            'old_shift': {
				'date': "May 10, 2023",
				'time':	"5:00 - 7:00 PM",
				'location': "ILC S211",
				'kind':	"SI"		
			},
            'new_shift': {
				'date': "May 12, 2023",
				'time':	"5:00 - 7:00 PM",
				'location': "ILC S211",
				'kind':	"SI"		
			},
		}
    )