from django import template

register = template.Library()

@register.filter
def to_colon(value):
    return value.replace(".", ":")