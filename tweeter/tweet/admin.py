from django.contrib import admin
from .models import Tweet
from .models import Comment, Collaborations
# Register your models here.
admin.site.register(Tweet)
admin.site.register(Comment)
admin.site.register(Collaborations)