# Generated by Django 5.1.7 on 2025-03-28 09:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0004_alter_profile_saved_items'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='saved_items',
            field=models.CharField(blank=True, default='[]', max_length=200, null=True),
        ),
    ]
