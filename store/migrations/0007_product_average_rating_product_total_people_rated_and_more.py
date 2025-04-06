# Generated by Django 5.1.7 on 2025-04-06 08:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0006_remove_order_customer_remove_order_product_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='average_rating',
            field=models.DecimalField(decimal_places=2, default=5.0, max_digits=3),
        ),
        migrations.AddField(
            model_name='product',
            name='total_people_rated',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='product',
            name='total_ratings_sum',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
