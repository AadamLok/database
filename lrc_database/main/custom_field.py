from datetime import timedelta

from django import forms
from django.db.models import Q
from .models import LRCDatabaseUser, Semester

class TypedModelListField(forms.ModelChoiceField):
	
    def to_python(self, value):
        if self.required:
            if value == '' or value == None:
                raise forms.ValidationError('Cannot be empty')
        try:
            value = int(value.split('[')[1][:-1])
            value = type(self.queryset[0]).objects.get(id=value)
        except:
            raise forms.ValidationError('Select a valid choice. That choice is not one of the available choices.')
        value = super().to_python(value)
        return value

    def __init__(self, *args, **kwargs):
        self.validate_field= kwargs.pop('validate_field', None)
        super().__init__(*args, **kwargs)

class ListTextWidget(forms.TextInput):
	
    def __init__(self, dataset, name, *args, **kwargs):
        super().__init__(*args)
        self._name = name
        self._list = dataset
        self.attrs.update({'list':'list__%s' % self._name})
        if 'identifier' in kwargs:
            self.attrs.update({'id':kwargs['identifier']})

    def render(self, name, value, attrs=None, renderer=None):
        text_html = super().render(name, value, attrs=attrs)
        data_list = '<datalist id="list__%s">' % self._name
        for item in self._list:
            data_list += f'<option value="{item} [{item.id}]"/>'
			# data_list += f'<option value="{item.id}">{item}</option>'
        data_list += '</datalist>'
        return (text_html + data_list)

class CustomDurationField(forms.fields.DurationField):
    def to_python(self, value):
        if self.required:
            if value == '' or value == None:
                raise forms.ValidationError('Cannot be empty')
        try:
            value += ":00"
        except:
            raise forms.ValidationError('Select a valid choice. That choice is not one of the available choices.')
        value = super().to_python(value)
        return value

    def __init__(self, *args, **kwargs):
        self.validate_field= kwargs.pop('validate_field', None)
        super().__init__(*args, **kwargs)