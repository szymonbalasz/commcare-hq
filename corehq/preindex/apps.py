from functools import partial

from django.apps import AppConfig


class Config(AppConfig):
    name = "corehq.preindex"

    def autodetect_migrations(self, add_operation):
        from dimagi.utils.couch.migration_operations import ReindexCouchViews
        from .django_migrations import (
            designs_did_change,
            iter_couch_lock_lines,
            write_designs_lock_file
        )
        lines = list(iter_couch_lock_lines())
        if designs_did_change(lines):
            add_operation(self.label, ReindexCouchViews())
            return partial(write_designs_lock_file, lines)
