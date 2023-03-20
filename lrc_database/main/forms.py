from django import forms
from django.contrib.auth.models import Group

from .custom_field import TypedModelListField, ListTextWidget, CustomDurationField

from .models import (
    ClassDetails, 
    Course, 
    DaySwitch, 
    FullCourse, 
    Hardware, 
    Holidays, 
    Loan, 
    LRCDatabaseUser, 
    Semester, 
    Shift, 
    ShiftChangeRequest, 
    StaffUserPosition
)

class LogIn(forms.Form):
    username = forms.CharField(label="Username", max_length=150, required=True)
    password = forms.CharField(label="Password", max_length=150, required=True, widget=forms.PasswordInput())

class ResetPassword(forms.Form):
    user = forms.ModelChoiceField(required=True, queryset=LRCDatabaseUser.objects.all())

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ("department", "number", "name")

class ReadOnlyFullCourseForm(forms.ModelForm):
    class Meta:
        model = FullCourse
        fields = ("semester", "course", "faculty")
        widgets = {
            'semester': forms.TextInput(attrs={'disabled': True}),
            'course': forms.TextInput(attrs={'disabled': True}),
            'faculty': forms.TextInput(attrs={'disabled': True}),
        }


class FullCourseForm(forms.ModelForm):
    class Meta:
        model = FullCourse
        fields = ("semester", "course", "faculty")

class ClassDetailsForm(forms.ModelForm):
    class Meta:
        model = ClassDetails
        fields = ("location", "class_day", "class_time", "class_duration")
        widgets = {
            "class_time": forms.TimeInput(attrs={'type': 'time'})
        }

class SemesterForm(forms.ModelForm):
    class Meta:
        model = Semester
        fields = ("name", "start_date", "end_date")
        widgets = {
            "start_date": forms.DateInput(attrs={'type': 'date'}),
            "end_date": forms.DateInput(attrs={'type': 'date'})
        }

class SemesterSelectForm(forms.Form):
    semester = forms.ModelChoiceField(required=True, queryset=Semester.objects.all())
    semester_select_form = forms.BooleanField(widget=forms.HiddenInput, initial=True)

    def __init__(self, *args, onchange=False, **kwargs):
        super(SemesterSelectForm, self).__init__(*args, **kwargs)
        if onchange:
            self.fields['semester'].widget.attrs = {"onchange":"this.form.submit()"}

class UserSelectForm(forms.Form):
    user = forms.ModelChoiceField(required=True, queryset=LRCDatabaseUser.objects.all())
    user_select_form = forms.BooleanField(widget=forms.HiddenInput, initial=True)

    def __init__(self, *args, onchange=False, **kwargs):
        super(UserSelectForm, self).__init__(*args, **kwargs)
        if onchange:
            self.fields['user'].widget.attrs = {"onchange":"this.form.submit()"}

class ReadOnlySemesterForm(forms.ModelForm):
    class Meta:
        model = Semester
        fields = ("name", "start_date", "end_date")
        widgets = {
            'name': forms.TextInput(attrs={'disabled': True}),
            'start_date': forms.TextInput(attrs={'disabled': True}),
            'end_date': forms.TextInput(attrs={'disabled': True}),
        }


class HolidaysForm(forms.ModelForm):
    class Meta:
        model = Holidays
        fields = ("date",)
        widgets = {
            "date": forms.DateInput(attrs={'type': 'date'}),
        }
    
    holiday_form = forms.BooleanField(widget=forms.HiddenInput, initial=True)

class DaySwitchForm(forms.ModelForm):
    class Meta:
        model = DaySwitch
        fields = ("date_of_switch", "day_to_follow")
        widgets = {
            "date_of_switch": forms.DateInput(attrs={'type': 'date'}),
        }
    
    day_switch_form = forms.BooleanField(widget=forms.HiddenInput, initial=True)

class CreateUserForm(forms.ModelForm):
    class Meta:
        model = LRCDatabaseUser
        fields = ("email", "first_name", "last_name")

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

class AddCoursesInBulkForm(forms.Form):
    course_data = forms.CharField(widget=forms.Textarea)

class EditProfileForm(forms.ModelForm):
    class Meta:
        model = LRCDatabaseUser
        fields = ("first_name", "last_name", "email")


class ApproveChangeRequestForm(forms.ModelForm):
    class Meta:
        model = Shift
        fields = ("position", "start", "duration", "location", "kind")


class SetToPendingForm(forms.ModelForm):
    class Meta:
        model = Shift
        fields = ("position", "start", "duration", "location", "kind")


class NewChangeRequestForm(forms.ModelForm):
    class Meta:
        model = ShiftChangeRequest
        fields = ("new_position","reason", "new_start", "new_duration", "new_location", "new_kind")

    def __init__(self, form_person = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if form_person is not None:
            active_positions = StaffUserPosition.objects.filter(person=form_person, semester=Semester.objects.get_active_sem()).all()
            self.fields["new_position"] = forms.ModelChoiceField(required=True, queryset=active_positions, label="New Position")

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
    position = TypedModelListField(queryset=StaffUserPosition.objects.all())
    duration = CustomDurationField(required=True)
    class Meta:
        model = Shift
        exclude = ('signed','reason','attended','late', 'late_datetime')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        dataset = StaffUserPosition.objects.filter(semester=Semester.objects.get_active_sem()).all()
        self.fields['position'].queryset = dataset
        self.fields['position'].widget = ListTextWidget(
            dataset=dataset, 
            name='position')

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
        exclude = ("start","signed","attended","reason", "late", "late_datetime")



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

class PayrollForm(forms.ModelForm):
    class Meta:
        model = Shift
        fields = ("attended","reason")
    
    def __init__(self, identifier, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields[f'form-{identifier}'] = forms.BooleanField(widget=forms.HiddenInput, initial=True)