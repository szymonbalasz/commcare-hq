# Generated by Django 3.2.15 on 2022-11-15 13:32

from django.db import migrations, models


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ('sms', '0053_alter_messagingsubevent_date_last_activity'),
    ]

    operations = [
        migrations.AddField(
            model_name='messagingsubevent',
            name='domain',
            field=models.CharField(max_length=126, null=True),
        ),
    ]