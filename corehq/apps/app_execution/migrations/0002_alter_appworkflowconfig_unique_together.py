# Generated by Django 3.2.25 on 2024-04-30 11:10

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app_execution', '0001_initial'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='appworkflowconfig',
            unique_together=set(),
        ),
    ]
