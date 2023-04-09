from django import template

register = template.Library()

@register.filter
def no_military(value):
    if ':' in value:
        array = value.split(":")
        hour = int(array[0])

        if hour > 12:
            hour = hour - 12
            array[0] = str(hour)
            ans = ":".join(array)
            ans += " pm"
            return ans
        else:
            value += " am"
            return value
    return value