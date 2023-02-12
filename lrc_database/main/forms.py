from django import forms
from django.contrib.auth.models import Group

from .models import ClassDetails, Course, DaySwitch, FullCourse, Hardware, Holidays, Loan, LRCDatabaseUser, Semester, Shift, ShiftChangeRequest, StaffUserPosition


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ("department", "number", "name")

class FullCourseForm(forms.ModelForm):
    class Meta:
        model = FullCourse
        fields = ("semester", "course", "faculty")

class ClassDetailsForm(forms.ModelForm):
    class Meta:
        model = ClassDetails
        fields = ("full_course", "location", "class_day", "class_time")

class SemesterForm(forms.ModelForm):
    class Meta:
        model = Semester
        fields = ("name", "start_date", "end_date")


class HolidaysForm(forms.ModelForm):
    class Meta:
        model = Holidays
        fields = ("semester","date")

class DaySwitchForm(forms.ModelForm):
    class Meta:
        model = DaySwitch
        fields = ("semester", "date_of_switch", "day_to_follow")

class CreateUserForm(forms.ModelForm):
    class Meta:
        model = LRCDatabaseUser
        fields = ("username", "email", "first_name", "last_name", "password")

    groups = forms.ModelMultipleChoiceField(queryset=Group.objects.all(), widget=forms.CheckboxSelectMultiple)

class EditUserForm(forms.ModelForm):
    class Meta:
        model = LRCDatabaseUser
        fields = ("username","first_name", "last_name", "email")
        widgets = {
            'username': forms.TextInput(attrs={'disabled': True}),
        }

    edit_user = forms.BooleanField(widget=forms.HiddenInput, initial=True)
    groups = forms.ModelMultipleChoiceField(queryset=Group.objects.all(), widget=forms.CheckboxSelectMultiple)

    def __init__(self, *args, **kwargs):
        super(EditUserForm, self).__init__(*args, **kwargs)
        if self.instance:
            self.fields['groups'].initial = self.instance.groups.all()

class StaffUserPositionForm(forms.ModelForm):
    class Meta:
        model = StaffUserPosition
        fields = ("semester", "position", "hourly_rate", "tutor_courses", "si_course", "peers")
    
    staff_position = forms.BooleanField(widget=forms.HiddenInput, initial=True)

class CreateUsersInBulkForm(forms.Form):
    user_data = forms.CharField(widget=forms.Textarea)


class EditProfileForm(forms.ModelForm):
    class Meta:
        model = LRCDatabaseUser
        fields = ("first_name", "last_name", "email")


class ApproveChangeRequestForm(forms.ModelForm):
    class Meta:
        model = Shift
        fields = ("associated_person", "start", "duration", "location", "kind")


class NewChangeRequestForm(forms.ModelForm):
    class Meta:
        model = ShiftChangeRequest
        fields = ("reason", "new_start", "new_duration", "new_location", "new_kind")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.fields["new_start"].widget = forms.DateTimeInput()


class NewDropRequestForm(forms.ModelForm):
    class Meta:
        model = ShiftChangeRequest
        fields = ("reason",)


class AddHardwareForm(forms.ModelForm):
    class Meta:
        model = Hardware
        fields = ("name", "is_available")
        widgets = {"name": forms.TextInput(attrs={"class": "form-control"})}


class NewShiftForm(forms.ModelForm):
    class Meta:
        model = Shift
        exclude = ()
class NewShiftRecurringForm(forms.ModelForm):
    shift_start_time = forms.TimeField(
        widget= forms.TimeInput(attrs={'type':'time'}))
    recurring_start_date = forms.DateField(
        help_text="Format: DD/MM/YYYY", 
        widget = forms.widgets.DateInput(attrs={'type': 'date'}))
    recurring_end_date = forms.DateField(
        help_text="Format: DD/MM/YYYY", 
        widget = forms.widgets.DateInput(attrs={'type': 'date'}))
    recurring_day_of_week = forms.ChoiceField(choices=[(0,"Monday"),(1,"Tuesday"),(2,"Wednesday"),(3,"Thurday"),(4,"Friday"),(5,"Saturday"),(6,"Sunday")])
    class Meta:
        model = Shift
        exclude = ("start",)


class NewShiftForTutorForm(forms.ModelForm):
    class Meta:
        model = Shift
        exclude = ("associated_person", "location", "kind")


class NewLoanForm(forms.ModelForm):
    start_time = forms.DateTimeField(
        input_formats=["%d/%m/%Y %H:%M"],
        widget=forms.DateTimeInput(format="%d/%m/%Y %H:%M", attrs={"class": "form-control"}),
        help_text="DD/MM/YYYY HH:MM",
    )
    return_time = forms.DateTimeField(
        input_formats=["%d/%m/%Y %H:%M"],
        widget=forms.DateTimeInput(format="%d/%m/%Y %H:%M", attrs={"class": "form-control"}),
        required=False,
        help_text="DD/MM/YYYY HH:MM",
    )
    target = forms.Select(attrs={"class": "form-control"})
    hardware_user = forms.Select(attrs={"class": "form-control"})

    class Meta:
        model = Loan
        fields = ("target", "hardware_user", "start_time", "return_time")
