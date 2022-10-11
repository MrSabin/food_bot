import calendar

from django.db import models
from django.db.models import F
from django.utils import timezone

FREE_RECIPES_ALLOWED = 3


class Diet(models.Model):
    title = models.CharField(max_length=255, verbose_name="Тип диеты")

    def __str__(self):
        return self.title


class Recipe(models.Model):
    title = models.CharField(max_length=255, verbose_name="Название блюда")
    diet = models.ForeignKey(Diet, on_delete=models.CASCADE, verbose_name="Тип диеты")
    ingredients = models.TextField(verbose_name="Ингредиенты")
    image = models.CharField(max_length=255, verbose_name="Изображение")
    description = models.TextField(verbose_name="Описание")

    def __str__(self):
        return self.title


class Customer(models.Model):
    user_id = models.IntegerField(verbose_name="Telegram ID")
    full_name = models.CharField(max_length=50, verbose_name="Полное имя")
    phone_number = models.CharField(
        max_length=30,
        verbose_name="Номер телефона",
        blank=True,
        default="",
    )
    favorite_recipes = models.ManyToManyField(Recipe, verbose_name='избранные рецепты', related_name="favorited_by")
    excluded_recipes = models.ManyToManyField(Recipe, verbose_name='скрытые рецепты', related_name="excluded_by")

    def __str__(self):
        return self.full_name

    def is_allowed_recipes(self):
        return self.subscription.is_active() or self.subscription.sent_free < FREE_RECIPES_ALLOWED

    def count_sent_recipe(self):
        if not self.subscription.is_active():
            self.subscription.sent_free = F('sent_free') + 1
            self.subscription.save()

    def add_free_subscription(self):
        self.subscription = Subscription(user=self)
        self.subscription.save()

    def renew_subscription(self):
        self.subscription.renewed_at = timezone.now()
        self.subscription.save()


class Subscription(models.Model):
    user = models.OneToOneField(Customer, on_delete=models.CASCADE)
    sent_free = models.IntegerField(verbose_name="Бесплатных отправлено", default=0)
    renewed_at = models.DateTimeField('когда обновлена', null=True, blank=True)

    def __str__(self):
        return f'Subscription of {self.user}, active: {self.is_active()}'

    def is_active(self):
        now = timezone.now()
        _, days_this_month = calendar.monthrange(now.year, now.month)
        if self.renewed_at is not None:
            return now - self.renewed_at <= timezone.timedelta(days=days_this_month)
        return False
