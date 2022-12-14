# Generated by Django 4.1.2 on 2022-10-09 21:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bot_db', '0009_alter_ingredient_group_alter_user_phone_number'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='excluded_recipes',
            field=models.ManyToManyField(related_name='excluded_by', to='bot_db.recipe'),
        ),
        migrations.AlterField(
            model_name='user',
            name='favorite_recipes',
            field=models.ManyToManyField(related_name='favorited_by', to='bot_db.recipe'),
        ),
    ]
