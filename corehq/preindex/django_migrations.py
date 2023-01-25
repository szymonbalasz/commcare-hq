import hashlib
import os
from operator import attrgetter
from pathlib import Path

from couchdbkit.designer import document

from .accessors import get_preindex_designs

LOCK_PATH = Path(__file__).parent / "couchviews.lock"
LOCK_PREAMBLE = """\
# This file is autogenerated every time a new "reindex" migration is
# generated by the `makemigrations` management command. If it becomes
# outdated it can be updated by running:
#
# ./manage.py makemigrations preindex
#
# The commcare-hq automated tests require that the contents of this
# file match the current Couch views list. If that check fails on a
# GitHub PR, the PR will not be eligible for merging. You can check if
# the current state of this file will pass automated tests by running:
#
# ./manage.py makemigrations preindex --check --dry-run
#
# NOTE: Some files listed here are not meant to be included in Couch
# design documents (e.g., Python source files), but are included as a
# result of a bug in corehq.couchapps.
#
"""


def iter_couch_lock_lines(preamble=LOCK_PREAMBLE):
    yield from preamble.splitlines(keepends=True)
    seen = set()
    corehq = Path(__file__).parent.parent
    assert corehq.name == "corehq", corehq
    rootlen = len(str(corehq.parent)) + 1
    for design in sorted(get_preindex_designs(), key=attrgetter("design_path")):
        doc = document(design.design_path).doc()
        for relpath in doc["couchapp"]["manifest"]:
            fullpath = os.path.join(design.design_path, relpath)
            viewpath = fullpath[rootlen:]
            if os.path.isdir(fullpath):
                continue
            sha = sha256sum(fullpath)[:20]
            if (sha, viewpath) not in seen:
                yield f"{sha} {viewpath}\n"
                seen.add((sha, viewpath))


def designs_did_change(lines, lock_path=LOCK_PATH):
    if not os.path.exists(lock_path):
        return True
    with open(lock_path, "r") as file:
        return list(file) != lines


def write_designs_lock_file(lines, lock_path=LOCK_PATH):
    """Write a new .lock file."""
    with open(lock_path, "w") as file:
        file.write("".join(lines))


def sha256sum(filename):
    # https://stackoverflow.com/a/44873382/10840
    h = hashlib.sha256()
    b = bytearray(128 * 1024)
    mv = memoryview(b)
    with open(filename, 'rb', buffering=0) as f:
        while n := f.readinto(mv):
            h.update(mv[:n])
    return h.hexdigest()
