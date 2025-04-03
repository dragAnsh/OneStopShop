# Generated by Django 5.1.7 on 2025-04-03 09:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payment', '0006_order_billing_address'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='payment_method',
            field=models.CharField(choices=[('PayPal', 'PayPal'), ('Stripe', 'Stripe'), ('COD', 'Cash On Delivery'), ('NA', 'NA')], max_length=6),
        ),
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('Pending', 'Pending'), ('Paid', 'Paid'), ('Payment Pending COD', 'Payment Pending COD')], default='Pending', max_length=20),
        ),
    ]
