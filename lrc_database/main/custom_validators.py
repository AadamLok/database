from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

import os

def validate_course_number(value):
    class_number = None
    try:
        class_number = "0"
        for c in value:
            if c.isdigit():
                class_number += c
            else:
                break
        print(class_number)
        class_number = int(class_number)
    except:
        raise ValidationError(_("First 3 characters of course number should be a number"))

    if class_number < 100 or class_number > 999:
        raise ValidationError(_("Course number should be between 100 and 999"))

def validate_file_extension(value):
    ext = os.path.splitext(value.name)[1]  # [0] returns path+filename
    valid_extensions = ['.pdf']
    if not ext.lower() in valid_extensions:
        raise ValidationError('Unsupported file extension.')