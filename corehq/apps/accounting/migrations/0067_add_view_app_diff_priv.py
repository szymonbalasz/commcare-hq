# Generated by Django 3.2.16 on 2023-02-03 06:57

from django.core.management import call_command
from django.db import migrations

from corehq import privileges
from corehq.util.django_migrations import skip_on_fresh_install


@skip_on_fresh_install
def _grandfather_view_app_diff_privs(apps, schema_editor):
    call_command('cchq_prbac_bootstrap')
    call_command(
        'cchq_prbac_grandfather_privs',
        privileges.VIEW_APP_DIFF,
        skip_edition='Paused,Community,Standard,Pro',
        noinput=True,
    )


class Migration(migrations.Migration):

    dependencies = [
        ('accounting', '0066_data_file_download_priv'),
    ]

    operations = [
        migrations.RunPython(_grandfather_view_app_diff_privs),
    ]