from django import template

register = template.Library()


@register.filter
def to_int_range(value):
    if "-" in value:
        array = value.split("-")
        return range(int(array[0]), int(array[1]) + 1)
