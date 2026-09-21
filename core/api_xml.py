from datetime import datetime
from pathlib import Path
import secrets
import xml.etree.ElementTree as ET

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt

from .models import User, Task, Reminder, Mesaj, AuditLog, RaportSupervizor

TOKEN_FILE = Path(settings.BASE_DIR) / ".api_read_token"


def _read_token():
    try:
        return TOKEN_FILE.read_text(encoding="utf-8").strip()
    except Exception:
        return ""


def _authorized(request):
    configured = _read_token()
    if not configured:
        return False

    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return False

    supplied = header[7:].strip()
    return secrets.compare_digest(configured, supplied)


def _text(parent, tag, value):
    node = ET.SubElement(parent, tag)

    if value is None:
        node.set("nil", "true")
        return node

    if isinstance(value, bool):
        node.text = "true" if value else "false"
    elif isinstance(value, datetime):
        node.text = value.isoformat(timespec="seconds")
    else:
        node.text = str(value)

    return node


def _xml_response(root, status=200):
    try:
        ET.indent(root, space="  ")
    except AttributeError:
        pass

    body = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    response = HttpResponse(
        body,
        status=status,
        content_type="application/xml; charset=utf-8",
    )

    response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response["Pragma"] = "no-cache"
    response["Expires"] = "0"
    response["X-Data-Source"] = "live-sqlite"
    response["X-Read-Only"] = "true"
    return response


def _error(code, message, status):
    root = ET.Element("error")
    _text(root, "code", code)
    _text(root, "message", message)
    return _xml_response(root, status=status)


def read_only_api(view_func):
    @csrf_exempt
    def wrapper(request, *args, **kwargs):
        if request.method != "GET":
            response = _error(
                "method_not_allowed",
                "This API is read-only. Only GET is permitted.",
                405,
            )
            response["Allow"] = "GET"
            return response

        if not _authorized(request):
            return _error(
                "unauthorized",
                "Missing or invalid read-only API token.",
                401,
            )

        return view_func(request, *args, **kwargs)

    return wrapper


def _base_root(name):
    root = ET.Element(name)
    root.set("generatedAt", datetime.now().isoformat(timespec="seconds"))
    root.set("source", "live")
    root.set("readOnly", "true")
    return root


def _serialize_user(parent, user):
    node = ET.SubElement(parent, "user")
    _text(node, "id", user.id)
    _text(node, "username", user.username)
    _text(node, "firstName", user.first_name)
    _text(node, "lastName", user.last_name)
    _text(node, "email", user.email)
    _text(node, "role", getattr(user, "role", ""))
    _text(node, "isActive", user.is_active)
    _text(node, "isStaff", user.is_staff)
    _text(node, "isSuperuser", user.is_superuser)
    _text(node, "lastLogin", user.last_login)
    _text(node, "dateJoined", user.date_joined)
    return node


def _serialize_task(parent, task):
    node = ET.SubElement(parent, "task")
    _text(node, "id", task.id)
    _text(node, "title", task.titlu)
    _text(node, "description", task.descriere)
    _text(node, "location", task.locatie)
    _text(node, "action", task.actiune)
    _text(node, "observations", task.observatii)
    _text(node, "completionReport", task.raport_finalizare)

    _text(node, "status", task.status)
    _text(node, "priority", task.prioritate)
    _text(node, "notificationSent", task.notificare_trimisa)

    _text(node, "createdAt", task.data_crearii)
    _text(node, "deadline", task.deadline)
    _text(node, "startedAt", task.data_inceperii)
    _text(node, "completedAt", task.data_finalizarii)

    _text(node, "startLatitude", task.latitudine_inceput)
    _text(node, "startLongitude", task.longitudine_inceput)

    _text(node, "lastPauseStartedAt", task.ultima_incepere_pauza)
    _text(node, "pausedSeconds", task.suma_pauze_secunde)
    _text(node, "workedSeconds", task.timp_lucrat_secunde)

    creator = ET.SubElement(node, "createdBy")
    if task.creat_de_id:
        _text(creator, "id", task.creat_de_id)
        _text(creator, "username", task.creat_de.username)
        _text(creator, "role", getattr(task.creat_de, "role", ""))

    supervisor = ET.SubElement(node, "supervisor")
    if task.supervizor_id:
        _text(supervisor, "id", task.supervizor_id)
        _text(supervisor, "username", task.supervizor.username)
        _text(supervisor, "role", getattr(task.supervizor, "role", ""))

    assigned = ET.SubElement(node, "assignedUsers")
    for user in task.atribuit_catre.all().order_by("id"):
        user_node = ET.SubElement(assigned, "user")
        _text(user_node, "id", user.id)
        _text(user_node, "username", user.username)
        _text(user_node, "firstName", user.first_name)
        _text(user_node, "lastName", user.last_name)
        _text(user_node, "role", getattr(user, "role", ""))

    return node


def _serialize_reminder(parent, reminder):
    node = ET.SubElement(parent, "reminder")
    _text(node, "id", reminder.id)
    _text(node, "title", reminder.titlu)
    _text(node, "details", reminder.detalii)
    _text(node, "reminderDate", reminder.data_reminder)
    _text(node, "createdAt", reminder.creat_la)
    _text(node, "completed", getattr(reminder, "finalizat", False))
    _text(node, "completedAt", getattr(reminder, "data_finalizarii", None))

    creator = ET.SubElement(node, "createdBy")
    _text(creator, "id", reminder.user_id)
    _text(creator, "username", reminder.user.username)
    _text(creator, "role", getattr(reminder.user, "role", ""))
    return node


def _serialize_message(parent, message):
    node = ET.SubElement(parent, "message")
    _text(node, "id", message.id)
    _text(node, "content", message.continut)
    _text(node, "sentAt", message.data_trimitere)
    _text(node, "read", message.citit)

    sender = ET.SubElement(node, "sender")
    _text(sender, "id", message.expeditor_id)
    _text(sender, "username", message.expeditor.username)

    recipient = ET.SubElement(node, "recipient")
    _text(recipient, "id", message.destinatar_id)
    _text(recipient, "username", message.destinatar.username)
    return node


def _serialize_audit(parent, item):
    node = ET.SubElement(parent, "auditEntry")
    _text(node, "id", item.id)
    _text(node, "ipAddress", item.ip_address)
    _text(node, "action", item.actiune)
    _text(node, "dateTime", item.data_ora)

    user_node = ET.SubElement(node, "user")
    if item.user_id:
        _text(user_node, "id", item.user_id)
        _text(user_node, "username", item.user.username)
        _text(user_node, "role", getattr(item.user, "role", ""))
    return node


def _serialize_report(parent, report):
    node = ET.SubElement(parent, "report")
    _text(node, "id", report.id)
    _text(node, "reportDate", report.data_raportului)
    _text(node, "workDone", report.ce_s_a_facut)
    _text(node, "workNotDone", report.ce_nu_s_a_facut)
    _text(node, "workStatus", report.stare_lucrare)

    task_node = ET.SubElement(node, "task")
    _text(task_node, "id", report.task_id)
    _text(task_node, "title", report.task.titlu)
    _text(task_node, "location", report.task.locatie)
    _text(task_node, "status", report.task.status)

    supervisor = ET.SubElement(node, "supervisor")
    _text(supervisor, "id", report.supervizor_id)
    _text(supervisor, "username", report.supervizor.username)

    evaluated = ET.SubElement(node, "evaluatedEmployee")
    if report.angajat_evaluat_id:
        _text(evaluated, "id", report.angajat_evaluat_id)
        _text(evaluated, "username", report.angajat_evaluat.username)
        _text(evaluated, "role", getattr(report.angajat_evaluat, "role", ""))

    return node


def _users_queryset():
    return User.objects.all().order_by("id")


def _tasks_queryset():
    return (
        Task.objects
        .select_related("creat_de", "supervizor")
        .prefetch_related("atribuit_catre")
        .all()
        .order_by("id")
    )


def _reminders_queryset():
    return Reminder.objects.select_related("user").all().order_by("id")


def _messages_queryset():
    return (
        Mesaj.objects
        .select_related("expeditor", "destinatar")
        .all()
        .order_by("id")
    )


def _audit_queryset():
    return AuditLog.objects.select_related("user").all().order_by("id")


def _reports_queryset():
    return (
        RaportSupervizor.objects
        .select_related("task", "supervizor", "angajat_evaluat")
        .all()
        .order_by("id")
    )


@read_only_api
def api_live(request):
    root = _base_root("taskManager")

    users_node = ET.SubElement(root, "users")
    for user in _users_queryset():
        _serialize_user(users_node, user)

    tasks_node = ET.SubElement(root, "tasks")
    for task in _tasks_queryset():
        _serialize_task(tasks_node, task)

    history_node = ET.SubElement(root, "history")
    for task in _tasks_queryset().filter(status="finalizat"):
        _serialize_task(history_node, task)

    reminders_node = ET.SubElement(root, "reminders")
    for reminder in _reminders_queryset():
        _serialize_reminder(reminders_node, reminder)

    messages_node = ET.SubElement(root, "messages")
    for message in _messages_queryset():
        _serialize_message(messages_node, message)

    reports_node = ET.SubElement(root, "reports")
    for report in _reports_queryset():
        _serialize_report(reports_node, report)

    audit_node = ET.SubElement(root, "audit")
    for item in _audit_queryset():
        _serialize_audit(audit_node, item)

    counts = ET.SubElement(root, "counts")
    _text(counts, "users", User.objects.count())
    _text(counts, "tasks", Task.objects.count())
    _text(counts, "completedTasks", Task.objects.filter(status="finalizat").count())
    _text(counts, "reminders", Reminder.objects.count())
    _text(counts, "messages", Mesaj.objects.count())
    _text(counts, "reports", RaportSupervizor.objects.count())
    _text(counts, "auditEntries", AuditLog.objects.count())

    return _xml_response(root)


@read_only_api
def api_users(request):
    root = _base_root("users")
    for user in _users_queryset():
        _serialize_user(root, user)
    return _xml_response(root)


@read_only_api
def api_user_detail(request, user_id):
    user = get_object_or_404(User, id=user_id)
    root = _base_root("userDetail")
    _serialize_user(root, user)
    return _xml_response(root)


@read_only_api
def api_tasks(request):
    root = _base_root("tasks")
    for task in _tasks_queryset():
        _serialize_task(root, task)
    return _xml_response(root)


@read_only_api
def api_task_detail(request, task_id):
    task = get_object_or_404(_tasks_queryset(), id=task_id)
    root = _base_root("taskDetail")
    _serialize_task(root, task)
    return _xml_response(root)


@read_only_api
def api_history(request):
    root = _base_root("history")
    for task in _tasks_queryset().filter(status="finalizat"):
        _serialize_task(root, task)
    return _xml_response(root)


@read_only_api
def api_reminders(request):
    root = _base_root("reminders")
    for reminder in _reminders_queryset():
        _serialize_reminder(root, reminder)
    return _xml_response(root)


@read_only_api
def api_reminder_detail(request, reminder_id):
    reminder = get_object_or_404(_reminders_queryset(), id=reminder_id)
    root = _base_root("reminderDetail")
    _serialize_reminder(root, reminder)
    return _xml_response(root)


@read_only_api
def api_messages(request):
    root = _base_root("messages")
    for message in _messages_queryset():
        _serialize_message(root, message)
    return _xml_response(root)


@read_only_api
def api_reports(request):
    root = _base_root("reports")
    for report in _reports_queryset():
        _serialize_report(root, report)
    return _xml_response(root)


@read_only_api
def api_report_detail(request, report_id):
    report = get_object_or_404(_reports_queryset(), id=report_id)
    root = _base_root("reportDetail")
    _serialize_report(root, report)
    return _xml_response(root)


@read_only_api
def api_audit(request):
    root = _base_root("audit")
    for item in _audit_queryset():
        _serialize_audit(root, item)
    return _xml_response(root)
