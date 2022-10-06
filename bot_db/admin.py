from django.contrib import admin
from .models import Diet, Meal, Ingredient, Product_group, User, Subscription

admin.site.register(Diet)
admin.site.register(Meal)
admin.site.register(Ingredient)
admin.site.register(Product_group)
admin.site.register(User)
admin.site.register(Subscription)
