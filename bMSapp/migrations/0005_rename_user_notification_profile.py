# Generated by Django 4.2 on 2023-04-23 12:29

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bMSapp', '0004_notification'),
    ]

    operations = [
        migrations.RenameField(
            model_name='notification',
            old_name='user',
            new_name='profile',
        ),
    ]
