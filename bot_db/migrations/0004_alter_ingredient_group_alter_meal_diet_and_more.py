# Generated by Django 4.1.2 on 2022-10-05 16:13

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bot_db', '0003_remove_ingredient_meals_meal_ingredients'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ingredient',
            name='group',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bot_db.product_group', verbose_name='Продуктовая группа'),
        ),
        migrations.AlterField(
            model_name='meal',
            name='diet',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bot_db.diet', verbose_name='Тип диеты'),
        ),
        migrations.AlterField(
            model_name='meal',
            name='ingredients',
            field=models.ManyToManyField(to='bot_db.ingredient', verbose_name='Ингредиенты'),
        ),
    ]