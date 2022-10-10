from django.contrib import admin
from .models import Diet, Recipe, Customer, Subscription

admin.site.register(Recipe)
admin.site.register(Customer)
admin.site.register(Subscription)
