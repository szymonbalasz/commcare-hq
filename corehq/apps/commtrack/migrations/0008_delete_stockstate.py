# Generated by Django 2.2.24 on 2021-09-22 14:27

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('commtrack', '0007_rename_sql_models'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],  # table to be deleted later
            state_operations=[
                migrations.DeleteModel(
                    name='StockState',
                ),
            ]
        ),
    ]
