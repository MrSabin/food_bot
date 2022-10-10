from django.db import models
from django.db.models import F


class Diet(models.Model):
    title = models.CharField(max_length=255, verbose_name="Тип диеты")

    def __str__(self):
        return self.title


class Recipe(models.Model):
    title = models.CharField(max_length=255, verbose_name="Название блюда")
    diet = models.ForeignKey(Diet, on_delete=models.CASCADE, verbose_name="Тип диеты")
    ingredients = models.TextField(verbose_name="Ингредиенты")
    image = models.ImageField(
        upload_to="recipes", null=True, blank=True, verbose_name="Изображение"
    )
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
    favorite_recipes = models.ManyToManyField(
        Recipe, related_name="favorited_by")
    excluded_recipes = models.ManyToManyField(
        Recipe, related_name="excluded_by")

    def __str__(self):
        return self.full_name

    def add_sent_recipe(self):
        if not self.subscription.is_active:
            self.subscription.sent_free = F('sent_free') + 1
            self.subscription.save()

    def add_free_subscription(self):
        self.subscription = Subscription(user=self, sent_free=0)
        self.subscription.save()

    def add_paid_subscription(self):
        self.subscription.is_active = True
        self.subscription.save()


class Subscription(models.Model):
    user = models.OneToOneField(Customer, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=False)
    sent_free = models.IntegerField(verbose_name="Бесплатных отправлено")
