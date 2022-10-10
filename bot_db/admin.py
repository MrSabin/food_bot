from django.contrib import admin
from .models import Diet, Recipe, User, Subscription

admin.site.register(Diet)
admin.site.register(Recipe)
admin.site.register(User)
admin.site.register(Subscription)
