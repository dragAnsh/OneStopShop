# Generated by Django 5.1.7 on 2025-04-02 12:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payment', '0002_order_phone'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='invoice_id',
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AddField(
            model_name='order',
            name='status',
            field=models.CharField(default='Pending', max_length=10),
        ),
    ]
