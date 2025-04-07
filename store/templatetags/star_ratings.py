from django import template
register = template.Library()


@register.filter(name='star_type')
def star_type(value, star_num):
    star_num = float(star_num)
    if star_num <= value:
        return "full"
    elif star_num > value and star_num - 1 < value:
        return "half"
    else:
        return "empty"