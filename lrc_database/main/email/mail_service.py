from django.core.mail import EmailMessage, send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone
from django.urls import reverse

from datetime import datetime, timedelta

from ..models import ShiftChangeRequest, Shift

def send_email():
	html_msg = render_to_string(
		'email/test.html', {
		"name": "Aadam",
		"reason": "Exam Review 1",
		"date": "Dec 1, 2023",
		"time": "10:00 - 12:00 AM",
		"location": "ILC S211",
		}
	)
	msg1 = EmailMessage(
		'Test',
		html_msg,
		'"LRC Database" <umass.learning.resource.center@gmail.com>',
		['alokhandwala@umass.edu','aadamlokhandwala786@gmail.com'],
		reply_to=['lrcsi@umass.edu']
	)
	msg2 = EmailMessage(
		'Test',
		html_msg,
		'"LRC Database" <umass.learning.resource.center@gmail.com>',
		['alokhandwala@umass.edu','aadamlokhandwala786@gmail.com'],
		reply_to=['lrcsi@umass.edu']
	)
	msg1.content_subtype = "html"
	msg2.content_subtype = "html"
	msg1.send()
	msg2.send()

def send_email_shift_req(id: int) -> None:
	req = ShiftChangeRequest.objects.get(id=id)
	user = req.new_position.person
	email_addr = user.email
	context = {
		'name': user.first_name,
		'reason': req.reason,
		'has_old_shift': False,
		'has_new_shift': False,
		'drop_req': req.is_drop_request,
		'url': f"https://lrcstaff.umass.edu{reverse('view_single_request',args=[id])}"
	}

	subject = f""

	if req.is_drop_request or req.shift_to_update is not None:
		context['has_old_shift'] = True
		shift = req.shift_to_update
		shift_datetime = timezone.localtime(shift.start)
		context['old_shift'] = {
			'date': shift_datetime.strftime("%b %d, %Y"),
			'time':	shift_datetime.strftime("%I:%M") + " - " + (shift_datetime+shift.duration).strftime("%I:%M %p"),
			'location': shift.location,
			'kind':	shift.kind		
		}
		subject = shift_datetime.strftime("%b %d, %Y")
		if req.is_drop_request:
			subject = "New Drop Request - " + subject
		else:
			subject = "New Update Request - " + subject
	
	if not req.is_drop_request:
		context['has_new_shift'] = True
		shift_datetime = timezone.localtime(req.new_start)
		shift_date_str = shift_datetime.strftime("%b %d, %Y")
		context['new_shift'] = {
			'date': shift_date_str,
			'time':	shift_datetime.strftime("%I:%M") + " - " + (shift_datetime+req.new_duration).strftime("%I:%M %p"),
			'location': req.new_location,
			'kind':	req.new_kind	
		}
		if len(subject) == 0:
			subject = f"New Shift Request - {shift_date_str}"
		else:
			subject += f" -> {shift_date_str}"
	
	html_msg = render_to_string('email/shift_request.html', context)

	email = EmailMessage(
		subject,
		html_msg,
		'"LRC Database" <umass.learning.resource.center@gmail.com>',
		[email_addr],
		reply_to=['lrcsi@umass.edu']
	)
	email.content_subtype = "html"
	email.send()