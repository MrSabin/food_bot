from django.db import models


class Diet(models.Model):
    title = models.CharField(max_length=255, verbose_name="Тип диеты")

    def __str__(self):
        return self.title


class Ingredient(models.Model):
    title = models.CharField(max_length=255, verbose_name="Название продукта")

    def __str__(self):
        return self.title


class Meal(models.Model):
    title = models.CharField(max_length=255, verbose_name="Название блюда")
    diet = models.ForeignKey(Diet, on_delete=models.CASCADE)

    def __str__(self):
        return self.title
