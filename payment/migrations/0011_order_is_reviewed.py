# Generated by Django 5.1.7 on 2025-04-06 10:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payment', '0010_remove_order_status_alter_order_payment_method'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='is_reviewed',
            field=models.BooleanField(default=False),
        ),
    ]
