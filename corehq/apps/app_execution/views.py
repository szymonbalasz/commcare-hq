from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from corehq.apps.app_execution import const
from corehq.apps.app_execution.api import execute_workflow
from corehq.apps.app_execution.data_model import EXAMPLE_WORKFLOW
from corehq.apps.app_execution.exceptions import AppExecutionError, FormplayerException
from corehq.apps.app_execution.forms import AppWorkflowConfigForm
from corehq.apps.app_execution.models import AppExecutionLog, AppWorkflowConfig
from corehq.apps.domain.decorators import require_superuser_or_contractor
from corehq.apps.hqadmin.views import get_hqadmin_base_context
from corehq.apps.hqwebapp.decorators import use_bootstrap5


@require_superuser_or_contractor
@use_bootstrap5
def workflow_list(request):
    workflows = AppWorkflowConfig.objects.all()
    _augment_with_logs(workflows)
    context = _get_context(
        request, "Automatically Executed App Workflows", reverse("app_execution:workflow_list"),
        workflows=workflows
    )
    return render(request, "app_execution/workflow_list.html", context)


def _augment_with_logs(workflows):
    """Add log records to each workflow object. Always at 10 even if there are less than 10 logs.
    """
    for workflow in workflows:
        log_status = [{}] * 10
        logs = AppExecutionLog.objects.filter(workflow=workflow).order_by("-started")[:10]
        for i, log in enumerate(logs):
            log_status[9 - i] = {"success": log.success, "id": log.id}
        workflow.last_n = log_status


@require_superuser_or_contractor
@use_bootstrap5
def new_workflow(request):
    form = AppWorkflowConfigForm(initial={
        "workflow": EXAMPLE_WORKFLOW, "run_every": 1, "form_mode": const.FORM_MODE_HUMAN
    })
    if request.method == "POST":
        form = AppWorkflowConfigForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("app_execution:workflow_list")

    context = _get_context(
        request, "New App Workflow", reverse("app_execution:new_workflow"),
        add_parent=True, form=form
    )
    return render(request, "app_execution/workflow_form.html", context)


@require_superuser_or_contractor
@use_bootstrap5
def edit_workflow(request, pk):
    config = get_object_or_404(AppWorkflowConfig, pk=pk)
    form = AppWorkflowConfigForm(instance=config)
    if request.method == "POST":
        form = AppWorkflowConfigForm(request.POST, instance=config)
        if form.is_valid():
            form.save()
            return redirect("app_execution:workflow_list")

    context = _get_context(
        request, f"Edit App Workflow: {config.name}", reverse("app_execution:edit_workflow", args=[pk]),
        add_parent=True, form=form
    )
    return render(request, "app_execution/workflow_form.html", context)


@require_superuser_or_contractor
@use_bootstrap5
def test_workflow(request, pk):
    config = get_object_or_404(AppWorkflowConfig, pk=pk)

    context = _get_context(
        request, f"Test App Workflow: {config.name}", reverse("app_execution:test_workflow", args=[pk]),
        add_parent=True, workflow=config
    )

    if request.method == "POST":
        session = config.get_formplayer_session()
        try:
            execute_workflow(session, config.workflow)
        except (AppExecutionError, FormplayerException) as e:
            context["error"] = str(e)
            context["success"] = False
        else:
            context["success"] = True

        context["result"] = True
        context["output"] = session.log.getvalue()
        context["workflow_json"] = config.workflow_json

    return render(request, "app_execution/workflow_test.html", context)


def _get_context(request, title, url, add_parent=False, **kwargs):
    parents = [{
        "title": "Auto App Execution",
        "url": reverse("app_execution:workflow_list"),
    }]
    context = get_hqadmin_base_context(request)
    context.update({
        "current_page": {
            "page_name": title,
            "title": title,
            "url": url,
            "parents": parents if add_parent else [],
        },
        "section": {"page_name": "Admin", "url": reverse("default_admin_report")},
    })
    return {**context, **kwargs}


@require_superuser_or_contractor
@use_bootstrap5
def workflow_log_list(request, pk):
    logs = AppExecutionLog.objects.filter(workflow_id=pk).order_by("-started").all()
    context = _get_context(
        request,
        "Automatically Executed App Workflow Logs",
        reverse("app_execution:workflow_logs", args=[pk]),
        add_parent=True,
        workflow=AppWorkflowConfig.objects.get(id=pk),
        logs=logs,
        total=logs.count(),
    )
    return render(request, "app_execution/workflow_log_list.html", context)


@require_superuser_or_contractor
@use_bootstrap5
def workflow_logs_json(request, pk):
    logs = AppExecutionLog.objects.filter(workflow_id=pk).order_by("-started").all()
    return JsonResponse({
        "logs": [
            {
                "id": log.id,
                "started": log.started.strftime("%Y-%m-%d %H:%M:%SZ"),
                "completed": log.completed.strftime("%Y-%m-%d %H:%M:%SZ") if log.completed else None,
                "success": log.success,
                "duration": str(log.duration) if log.duration else "",
                "url": reverse("app_execution:workflow_log", args=[log.id])
            }
            for log in logs
        ]
    })


@require_superuser_or_contractor
@use_bootstrap5
def workflow_log(request, pk):
    log = get_object_or_404(AppExecutionLog, pk=pk)
    return render(
        request, "app_execution/workflow_log.html",
        _get_context(
            request,
            f"Workflow Log: {log.workflow.name}",
            reverse("app_execution:workflow_log", args=[pk]),
            add_parent=True,
            log=log,
            workflow_json=log.workflow.workflow_json
        )
    )
