# -*- coding: utf-8 -*-
# Generated by Django 1.11.27 on 2020-03-12 20:09
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_manager', '0013_rename_sqlglobalappconfig'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExchangeApplication',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('domain', models.CharField(max_length=255)),
                ('app_id', models.CharField(max_length=255)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='exchangeapplication',
            unique_together=set([('domain', 'app_id')]),
        ),
    ]
