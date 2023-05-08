from django.core.mail import EmailMessage, send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

def send_email():
    return
    html_msg = render_to_string(
        'email/test.html', {
            "name": "Aadam",
            "reason": "Exam Review 1",
            "date": "Dec 1, 2023",
            "time": "10:00 - 12:00 AM",
            "location": "ILC S211",
		}
    )
    msg = EmailMessage(
        'Final Test',
        html_msg,
        '"LRC Database" <umass.learning.resource.center@gmail.com>',
        ['alokhandwala@umass.edu','aadamlokhandwala786@gmail.com'],
        reply_to=['lrcsi@umass.edu']
	)
    msg.content_subtype = "html"
    msg.send()