from django import template

register = template.Library()

@register.filter
def user_liked(like_queryset, user):
    return like_queryset.filter(id=user.id).exists()
