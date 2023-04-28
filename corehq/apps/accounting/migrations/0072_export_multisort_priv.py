# Generated by Django 3.2.16 on 2023-04-05 06:55

from django.core.management import call_command
from django.db import migrations

from corehq.apps.accounting.models import SoftwarePlanEdition
from corehq.privileges import EXPORT_MULTISORT
from corehq.util.django_migrations import skip_on_fresh_install


@skip_on_fresh_install
def _grandfather_export_multisort_priv(apps, schema_editor):
    call_command('cchq_prbac_bootstrap')

    # EXPORT_MULTISORT are Standard Plan and higher
    skip_editions = ','.join((
        SoftwarePlanEdition.PAUSED,
        SoftwarePlanEdition.COMMUNITY,
    ))
    call_command(
        'cchq_prbac_grandfather_privs',
        EXPORT_MULTISORT,
        skip_edition=skip_editions,
        noinput=True,
    )


class Migration(migrations.Migration):

    dependencies = [
        ('accounting', '0071_add_billingaccountwebuserhistory'),
    ]

    operations = [
        migrations.RunPython(
            _grandfather_export_multisort_priv,
            reverse_code=migrations.RunPython.noop,
        ),
    ]