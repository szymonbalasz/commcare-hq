import csv

from django.core.management.base import BaseCommand, CommandError
from corehq.apps.app_manager.models import Application
from casexml.apps.case.xform import get_case_ids_from_form
from corehq.form_processor.interfaces.dbaccessors import FormAccessors, CaseAccessors
from dimagi.utils.django.management import are_you_sure
from datetime import datetime


XFORM_HEADER = ['Version', 'Form Id', 'Domain']
CASE_HEADER = ['CaseID', 'CaseType', 'CaseOpenedOn', 'CaseName', 'CaseUserId', 'CaseXFormIds']
CURRENT_TIME = datetime.strftime(datetime.now(), '-%Y-%m-%d-%H:%M:%S')
XFORM_FILENAME = "XForm-Details%s.csv" % CURRENT_TIME
CASE_FILE_NAME = 'Case-Details%s.csv' % CURRENT_TIME



class Command(BaseCommand):
    help = """Expects 4 arguments in order : domain app_id version_number test_run
ex: ./manage.py purge_forms_and_cases testapp c531daeece0633738c9a3676a13e3d4f 88 yes
domain is included with app_id to ensure the user knows what app to delete
version_number to delete data accumulated by versions BEFORE this : integer
test_run should be yes(case-sensitive) for a test_run and anything otherwise
though deletion would be re-confirmed so dont panic
"""

    def __init__(self):
        super(Command, self).__init__()
        self.case_ids = set()
        self.filtered_xform_ids, self.xform_ids = [], []
        self.xform_writer, self.case_writer = None, None
        self.forms_accessor, self.case_accessors = None, None
        self.domain, self.app_id, self.version_number, self.test_run = None, None, None, None

    def setup(self):
        self.xform_writer = csv.writer(open(XFORM_FILENAME, 'w+b'))
        self.xform_writer.writerow(XFORM_HEADER)
        self.case_writer = csv.writer(open(CASE_FILE_NAME, 'w+b'))
        self.case_writer.writerow(CASE_HEADER)
        self.forms_accessor = FormAccessors(self.domain)
        self.case_accessors = CaseAccessors(self.domain)

    def ensure_prerequisites(self, args):
        if len(args) != 4:
            raise CommandError('Arguments number mismatch')
        self.domain = args[0]
        self.app_id = args[1]
        self.version_number = int(args[2])
        self.test_run = True if args[3] == 'yes' else False
        _notify_parsed_args(*args)
        app = Application.get(self.app_id)
        if app.domain != self.domain:
            raise CommandError('Domain not same as from app id')
        self.setup()

    def handle(self, *args, **options):
        self.ensure_prerequisites(args)
        self.xform_ids = self.forms_accessor.get_all_form_ids_in_domain()
        self.iterate_forms_and_collect_case_ids()
        _print_final_debug_info(self.xform_ids, self.filtered_xform_ids, self.case_ids)
        if self.data_to_delete() and self.delete_permitted():
            self.delete_forms_and_cases()
            print "Process Completed!! Keep copy of files %s, %s" % (XFORM_FILENAME, CASE_FILE_NAME)
        else:
            print 'Process Finished w/o Changes..'

    def iterate_forms_and_collect_case_ids(self):
        print "Iterating Through %s XForms and Collecting Case Ids" % len(self.xform_ids)
        for xform in self.forms_accessor.iter_forms(self.xform_ids):
            _print_form_details(xform, self.xform_writer)
            if '@version' in xform.form and int(xform.form['@version']) < self.version_number:
                self.ensure_valid_xform(xform)
                self.filtered_xform_ids.append(xform.form_id)
                self.case_ids = self.case_ids.union(get_case_ids_from_form(xform))
            else:
                print 'skipping xform id: %s' % xform.form_id
        if self.case_ids:
            self.print_case_details()

    def ensure_valid_xform(self, xform):
        if xform.app_id != self.app_id and xform.domain != self.domain:
            _raise_xform_domain_mismatch(xform)

    def print_case_details(self):
        for case in self.case_accessors.iter_cases(self.case_ids):
            _print_case_details(case, self.case_writer)

    def delete_permitted(self):
        return not self.test_run and are_you_sure()

    def data_to_delete(self):
        return len(self.filtered_xform_ids) != 0 or len(self.case_ids) != 0

    def delete_forms_and_cases(self):
        print 'Proceeding with deleting forms and cases'
        self.forms_accessor.soft_delete_forms(self.filtered_xform_ids)
        self.case_accessors.soft_delete_cases(list(self.case_ids))


def _print_form_details(xform, file_writer):
    print XFORM_HEADER
    form_details = _form_details(xform)
    file_writer.writerow(form_details)
    print form_details


def _form_details(xform):
    return [xform.form.get('@version'), xform.form_id, xform.domain]


def _print_case_details(case, file_writer):
    print CASE_HEADER
    case_details = _case_details(case)
    file_writer.writerow(case_details)
    print case_details


def _case_details(case):
    return [case.get_id, case.type, str(case.opened_on), case.name, case.user_id, case.xform_ids]


def _raise_xform_domain_mismatch(xform):
    print "XForm app_id %s" % xform.app_id
    print "XForm domain %s" % xform.domain
    raise CommandError("XForm didn't match with app_id or domain")


def _print_final_debug_info(xform_ids, filtered_xform_ids, case_ids):
    print "Final Debug Info:"
    print "Form Ids Total(%i) :" % len(xform_ids), xform_ids
    print "Filtered Form Ids(%i) :" % len(filtered_xform_ids), filtered_xform_ids
    print "Case Ids(%i) :" % len(case_ids), case_ids


def _notify_parsed_args(domain_name, app_id, version_number, test_run):
    print 'Received request for domain : %s with app_id : %s to soft delete data before version number %s' % \
          (domain_name, app_id, version_number)
    print 'Test run : %s' % test_run
