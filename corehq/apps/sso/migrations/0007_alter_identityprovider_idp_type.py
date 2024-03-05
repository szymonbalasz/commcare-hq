# Generated by Django 3.2.24 on 2024-03-05 16:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sso', '0006_add_new_fields_in_identityprovider'),
    ]

    operations = [
        migrations.AlterField(
            model_name='identityprovider',
            name='idp_type',
            field=models.CharField(choices=[('azure_ad', 'Entra ID'), ('one_login', 'One Login'), ('okta', 'Okta')], default='azure_ad', max_length=50),
        ),
    ]
