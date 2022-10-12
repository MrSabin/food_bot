# Generated by Django 4.1.2 on 2022-10-11 23:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bot_db', '0014_alter_recipe_image'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='subscription',
            name='is_active',
        ),
        migrations.AddField(
            model_name='subscription',
            name='renewed_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='когда обновлена'),
        ),
        migrations.AlterField(
            model_name='customer',
            name='excluded_recipes',
            field=models.ManyToManyField(related_name='excluded_by', to='bot_db.recipe', verbose_name='скрытые рецепты'),
        ),
        migrations.AlterField(
            model_name='customer',
            name='favorite_recipes',
            field=models.ManyToManyField(related_name='favorited_by', to='bot_db.recipe', verbose_name='избранные рецепты'),
        ),
        migrations.AlterField(
            model_name='subscription',
            name='sent_free',
            field=models.IntegerField(default=0, verbose_name='Бесплатных отправлено'),
        ),
    ]
