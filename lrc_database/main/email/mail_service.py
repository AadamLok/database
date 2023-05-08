from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

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
    send_mail(
        'Testing',
        strip_tags(html_msg),
        '"LRC Database" <umass.learning.resource.center@gmail.com>',
        ['alokhandwala@umass.edu'],
        html_message=html_msg
	)