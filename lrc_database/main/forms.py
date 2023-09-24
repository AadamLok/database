from django import forms
from django.contrib.auth.models import Group

from .custom_field import TypedModelListField, ListTextWidget, CustomDurationField
from django.core.validators import FileExtensionValidator

from .custom_validators import validate_file_extension

from .models import (
    ClassDetails, 
    Course,
    CrossListed, 
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

class CrossListedForm(forms.ModelForm):
    class Meta:
        model = CrossListed
        fields = ("main_course", "department", "number", "name")

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

    def __init__(self, *args, **kwargs):
        super(StaffUserPositionForm, self).__init__(*args, **kwargs)
        self.fields["semester"].widget.attrs['id'] = "supf-sem"
        self.fields["position"].widget.attrs['id'] = "supf-pos"
        self.fields["tutor_courses"].widget.attrs['id'] = "supf-tc"
        self.fields["si_course"].widget.attrs['id'] = "supf-sic"
        self.fields["peers"].widget.attrs['id'] = "supf-peers"
        self.fields["tutor_courses"].widget.attrs['disabled'] = True
        self.fields["si_course"].widget.attrs['disabled'] = True
        self.fields["peers"].widget.attrs['disabled'] = True
    
    staff_position = forms.BooleanField(widget=forms.HiddenInput, initial=True)

class CreateUsersInBulkForm(forms.Form):
    user_data = forms.CharField(widget=forms.Textarea)

class AddCoursesInBulkForm(forms.Form):
    course_data = forms.CharField(widget=forms.Textarea)

class AddCourseSectionsInBulkForm(forms.Form):
    course_data = forms.CharField(widget=forms.Textarea)

class AddClassDetailsInBulkForm(forms.Form):
    class_data = forms.CharField(widget=forms.Textarea)

class EditProfileForm(forms.ModelForm):
    class Meta:
        model = LRCDatabaseUser
        fields = ("first_name", "last_name", "email")


class ApproveChangeRequestForm(forms.ModelForm):
    class Meta:
        model = Shift
        fields = ("position", "start", "duration", "location", "kind", "document")


class SetToPendingForm(forms.ModelForm):
    class Meta:
        model = Shift
        fields = ("position", "start", "duration", "location", "kind")


class NewChangeRequestForm(forms.ModelForm):
    new_duration = CustomDurationField(required=True, help_text="How long the shift will last.\
                                    Format: HH:MM. E.g. if you want shift to be 1 hour 15 mins long, enter 01:15")
    class Meta:
        model = ShiftChangeRequest
        fields = ("new_position","reason", "new_start", "new_location", "new_kind")

    def __init__(self, *args, form_person = None, **kwargs):
        super().__init__(*args, **kwargs)
        if form_person is not None:
            active_positions = StaffUserPosition.objects.filter(person=form_person, semester=Semester.objects.get_active_sem()).all()
            self.fields["new_position"] = forms.ModelChoiceField(required=True, queryset=active_positions, label="New Position")


class ExamReviewForm(forms.ModelForm):
    new_duration = CustomDurationField(required=True, help_text="How long the shift will last.\
                                    Format: HH:MM. E.g. if you want shift to be 1 hour 15 mins long, enter 01:15")
    class Meta:
        model = ShiftChangeRequest
        fields = ("new_position","reason", "new_start", "new_location", "new_kind")

    def __init__(self, *args, form_person = None, **kwargs):
        super().__init__(*args, **kwargs)
        if form_person is not None:
            active_positions = StaffUserPosition.objects.filter(person=form_person, semester=Semester.objects.get_active_sem()).all()
            self.fields["new_position"] = forms.ModelChoiceField(required=True, queryset=active_positions, label="New Position")
            
        self.fields["new_position"].widget.attrs['disabled'] = True
        self.fields["reason"].widget.attrs['disabled'] = True
        self.fields["new_start"].widget.attrs['disabled'] = True
        self.fields["new_location"].widget.attrs['disabled'] = True
        self.fields["new_kind"].widget.attrs['disabled'] = True
        self.fields["new_duration"].widget.attrs['disabled'] = True

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
    duration = CustomDurationField(required=True, help_text="How long the shift will last.\
                                    Format: HH:MM. E.g. if you want shift to be 1 hour 15 mins long, enter 01:15")
    class Meta:
        model = Shift
        exclude = ('signed','reason','attended','late', 'late_datetime', 'deleted')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        dataset = StaffUserPosition.objects.filter(semester=Semester.objects.get_active_sem()).all()
        self.fields['position'].queryset = dataset
        self.fields['position'].widget = ListTextWidget(
            dataset=dataset, 
            name='position')

class NewShiftRecurringForm(forms.ModelForm):
    duration = CustomDurationField(required=True, help_text="How long the shift will last.\
                                    Format: HH:MM. E.g. if you want shift to be 1 hour 15 mins long, enter 01:15")
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
        exclude = ("start","signed","attended","reason", "late", "late_datetime", "deleted","document")

class PMAddMeetingForm(forms.ModelForm):
    position = TypedModelListField(queryset=StaffUserPosition.objects.all(), help_text="Which of your peer are you meeting with?\
                                   Be careful and select appropriate postion of your peer.")
    duration = CustomDurationField(required=True, help_text="How long the shift will last.\
                                    Format: HH:MM. E.g. if you want shift to be 1 hour 15 mins long, enter 01:15")
    class Meta:
        model = Shift
        fields = ("position", "duration", "start", "location")
    
    def __init__(self, pm=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        dataset = StaffUserPosition.objects.filter(person__in=pm.peers_list())
        self.fields['position'].queryset = dataset
        self.fields['position'].widget = ListTextWidget(
            dataset=dataset, 
            name='position')

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

class DateSelectForm(forms.Form):
    date = forms.DateField(
        help_text="Format: DD/MM/YYYY", 
        widget = forms.widgets.DateInput(attrs={'type': 'date'}))
    
    def __init__(self, *args, **kwargs):
        super(DateSelectForm, self).__init__(*args, **kwargs)
        self.fields['date'].widget.attrs = {"onchange":"this.form.submit()"}
    
class UnknownForm(forms.Form):
    staff = StaffUserPosition.objects.filter(semester=Semester.objects.get_active_sem())

    si = forms.ModelMultipleChoiceField(
        queryset=staff.filter(position="SI"), 
        widget=forms.CheckboxSelectMultiple,
        label="SI Leaders",
    )

    gt = forms.ModelMultipleChoiceField(
        queryset=staff.filter(position="GT"), 
        widget=forms.CheckboxSelectMultiple,
        label="Group Tutors",
    )

    tutor = forms.ModelMultipleChoiceField(
        queryset=staff.filter(position="Tutor"), 
        widget=forms.CheckboxSelectMultiple,
        label="Tutors",
    )

    oursm = forms.ModelMultipleChoiceField(
        queryset=staff.filter(position="OursM"), 
        widget=forms.CheckboxSelectMultiple,
        label="OURS Mentor",
    )

    oa = forms.ModelMultipleChoiceField(
        queryset=staff.filter(position="OA"), 
        widget=forms.CheckboxSelectMultiple,
        label="Office Assistant",
    )

    tech = forms.ModelMultipleChoiceField(
        queryset=staff.filter(position="Tech"), 
        widget=forms.CheckboxSelectMultiple,
        label="Tech",
    )

    other = forms.ModelMultipleChoiceField(
        queryset=staff.filter(position="Other"), 
        widget=forms.CheckboxSelectMultiple,
        label="Others",
    )