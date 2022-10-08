from django.contrib import admin
from .models import Diet, Recipe, Ingredient, ProductGroup, User, Subscription

admin.site.register(Diet)
admin.site.register(Recipe)
admin.site.register(Ingredient)
admin.site.register(ProductGroup)
admin.site.register(User)
admin.site.register(Subscription)
