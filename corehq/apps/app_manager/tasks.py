from django.utils.translation import ugettext as _

from celery.task import task
from celery.utils.log import get_task_logger

from corehq.apps.app_manager.dbaccessors import (
    get_app,
    get_auto_generated_built_apps,
    get_latest_build_id,
)
from corehq.apps.app_manager.exceptions import SavedAppBuildException, AppValidationError
from corehq.apps.users.models import CommCareUser, CouchUser
from corehq.toggles import USH_USERCASES_FOR_WEB_USERS
from corehq.util.decorators import serial_task

logger = get_task_logger(__name__)


@task(queue='background_queue', ignore_result=True)
def create_usercases(domain_name):
    from corehq.apps.callcenter.sync_usercase import sync_usercase
    if USH_USERCASES_FOR_WEB_USERS.enabled(domain_name):
        users = CouchUser.by_domain(domain_name)
    else:
        users = CommCareUser.by_domain(domain_name)
    for user in users:
        sync_usercase(user, domain_name)


# Can be deleted after deploy
@serial_task('{app_id}-{version}', max_retries=0, timeout=60 * 60)
def make_async_build_v2(app_id, domain, version, allow_prune=True, comment=None):
    app = get_app(domain, app_id)
    try:
        copy = app.make_build(comment=comment)
    except AppValidationError:
        return
    copy.is_auto_generated = allow_prune
    copy.save(increment_version=False)
    return copy


def autogenerate_build(app, username):
    comment = _('Auto-generated by a phone update. Will expire after next build if not marked released. '
                'Generated by user {}.').format(username)
    latest_build = app.get_latest_build()
    if not latest_build or latest_build.version != app.version:
        autogenerate_build_task.delay(app.get_id, app.domain, app.version, comment)


@serial_task('{app_id}-{version}', max_retries=0, timeout=60 * 60)
def autogenerate_build_task(app_id, domain, version, comment):
    make_async_build_v2(app_id, domain, version, allow_prune=True, comment=comment)


@task(queue='background_queue', ignore_result=True)
def create_build_files_for_all_app_profiles(domain, build_id):
    app = get_app(domain, build_id)
    build_profiles = app.build_profiles
    save_app = False
    for profile in build_profiles:
        if not app.has_attachment('files/{id}/profile.xml'.format(id=profile)):
            app.create_build_files(build_profile_id=profile)
            save_app = True
    if save_app:
        app.save()


@task(queue='background_queue')
def prune_auto_generated_builds(domain, app_id):
    last_build_id = get_latest_build_id(domain, app_id)
    saved_builds = get_auto_generated_built_apps(domain, app_id)

    for doc in saved_builds:
        app = get_app(domain, doc['_id'])
        if app.id == last_build_id or app.is_released:
            continue
        if not app.is_auto_generated or app.copy_of != app_id or app.id == last_build_id:
            raise SavedAppBuildException("Attempted to delete build that should not be deleted")
        app.delete_app()
        logger.info("Pruned build {} from domain {}".format(app.id, domain))
        app.save(increment_version=False)


@task(queue='background_queue', ignore_result=True)
def update_linked_app_and_notify_task(domain, app_id, master_app_id, user_id, email):
    from corehq.apps.app_manager.views.utils import update_linked_app_and_notify
    update_linked_app_and_notify(domain, app_id, master_app_id, user_id, email)


@task
def load_appcues_template_app(domain, username, app_slug):
    from corehq.apps.app_manager.views.apps import load_app_from_slug
    load_app_from_slug(domain, username, app_slug)
