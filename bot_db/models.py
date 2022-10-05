from django.db import models


class Diet(models.Model):
    title = models.CharField(max_length=255, verbose_name="Тип диеты")

    def __str__(self):
        return self.title


class Product_group(models.Model):
    title = models.CharField(max_length=255, verbose_name="Группа продуктов")

    def __str__(self):
        return self.title


class Ingredient(models.Model):
    title = models.CharField(max_length=255, verbose_name="Название продукта")
    group = models.ForeignKey(
        Product_group, on_delete=models.CASCADE, verbose_name="Продуктовая группа"
    )

    def __str__(self):
        return self.title


class Meal(models.Model):
    title = models.CharField(max_length=255, verbose_name="Название блюда")
    diet = models.ForeignKey(
        Diet, on_delete=models.CASCADE, verbose_name="Тип диеты")
    ingredients = models.ManyToManyField(
        Ingredient, verbose_name="Ингредиенты")

    def __str__(self):
        return self.title
