import os
import sys
from io import StringIO
from textwrap import dedent

from django.conf import settings
from django.core.management.base import CommandError, no_translations
from django.core.management.commands import makemigrations, showmigrations

from corehq.util.django_migrations import patch_migration_autodetector


class Command(makemigrations.Command):

    LOCK_PATH = os.path.join(settings.BASE_DIR, "migrations.lock")
    LOCK_PREAMBLE = dedent("""\
        # This file is autogenerated every time Django migrations are written
        # by the `makemigrations` management command.
        # You can also update it to match current migrations by executing:
        #
        # ./manage.py makemigrations --lock-update
        #
        # The commcare-hq automated tests require that the contents of this file
        # match the current Django migrations list. If that check fails on a
        # GitHub PR, the PR will not be eligible for merging. You can check if
        # the current state of this file will pass automated tests by executing:
        #
        # ./manage.py makemigrations --lock-check
        #
        # Although integrated into the Django `makemigrations` utility, this
        # file is not part of the Django ecosystem. It is a migration safety
        # feature added by commcare-hq.
        # See: ./hqscripts/management/commands/makemigrations.py
        #
    """)

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            "--lock-path", metavar="FILE", default=self.LOCK_PATH,
            help="Read/write lock file %(metavar)s (default=%(default)s).",
        )
        parser.add_argument(
            "--lock-check", action="store_true",
            help="Exit with a non-zero status if the lock file is inconsistent.",
        )
        parser.add_argument(
            "--lock-update", action="store_true",
            help="Write a new (updated) lock file and exit.",
        )

    @no_translations
    def handle(self, *app_labels, **options):
        def assert_exclusive_options(opt_name, extra=[]):
            prevent = extra + ["dry_run", "merge", "empty", "name", "check_changes"]
            enforce = ["interactive", "include_header"]  # default=True
            if app_labels or any(options[k] for k in prevent) or not all(options[k] for k in enforce):
                raise CommandError(f"{opt_name} does not support other options besides --lock-path")

        self.lock_path = options["lock_path"]
        if options["lock_check"]:
            assert_exclusive_options("--lock-check", ["lock_update"])
            if not self.check_migrations_lock():
                self.stderr.write("Migrations lock file does not match migrations list.")
                sys.exit(1)
            self.stdout.write("Migrations lock file is up-to-date.")
        elif options["lock_update"]:
            assert_exclusive_options("--lock-update", ["lock_check"])
            self.write_migrations_lock()
        else:
            with patch_migration_autodetector(self):
                super().handle(*app_labels, **options)

    def write_migration_files(self, changes):
        super().write_migration_files(changes)
        if not self.dry_run:
            self.write_migrations_lock()

    def get_migrations_list(self, preamble=LOCK_PREAMBLE):
        """Generate and return the full list of existing migrations.

        :param preamble: String which will become the first line(s) of the
                         returned migration list.
        """
        stream = StringIO()
        # NOTE: showmigrations will exclude initial migrations for apps
        # that had a "migrations" directory without an __init__.py file
        # (a namespace package) prior to running "makemigrations" because of
        # https://github.com/django/django/blob/2b1242abb3989f5d74e787b091/django/db/migrations/loader.py#L99-L106
        command = showmigrations.Command(stdout=stream, no_color=True)
        # Use `run_from_argv()` to avoid extra command setup boilerplate.
        # First two argv items are `prog` and `subcommand`, used to setup the
        # command's argument parser, leaving them empty because it works.
        command.run_from_argv(["", "", "--list"])
        stream.seek(0)
        lines = preamble.splitlines(keepends=True)
        # strip the applied status off the front of migration lines
        for line in stream:
            if line[:5] in {" [ ] ", " [X] "}:
                line = line[4:]  # leave a leading space
            lines.append(line)
        return lines

    def write_migrations_lock(self):
        """Write a new migrations.lock file."""
        with open(self.lock_path, "w") as file:
            file.write("".join(self.get_migrations_list()))

    def check_migrations_lock(self):
        """Check if the current migrations list matches the migrations.lock."""
        with open(self.lock_path, "r") as file:
            frozen = list(file)
        current = self.get_migrations_list()
        return frozen == current
