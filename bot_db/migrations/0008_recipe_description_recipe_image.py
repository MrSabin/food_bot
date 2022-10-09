# Generated by Django 4.1.2 on 2022-10-09 05:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bot_db', '0007_rename_product_group_productgroup_rename_meal_recipe_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='recipe',
            name='description',
            field=models.TextField(default='', verbose_name='Описание'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='recipe',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='recipes', verbose_name='Изображение'),
        ),
    ]
