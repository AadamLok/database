from django.template import Library

register = Library()

@register.filter(name='startswith')
def startswith(text, starts):
    return text.startswith(starts)