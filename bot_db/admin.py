from django.contrib import admin
from .models import Recipe, User, Subscription

admin.site.register(Recipe)
admin.site.register(User)
admin.site.register(Subscription)
