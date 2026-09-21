from pathlib import Path
import secrets
import shutil
import sys
from datetime import datetime

ROOT = Path(__file__).resolve().parent
CORE = ROOT / "core"
URLS = CORE / "urls.py"
API_FILE = CORE / "api_xml.py"
TOKEN_FILE = ROOT / ".api_read_token"
GITIGNORE = ROOT / ".gitignore"

if not (ROOT / "manage.py").exists():
    print("EROARE: Pune acest script in acelasi folder cu manage.py.")
    sys.exit(1)

if not URLS.exists():
    print("EROARE: Nu gasesc core/urls.py")
    sys.exit(1)

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_dir = ROOT / f"backup_api_xml_{stamp}"
backup_dir.mkdir(exist_ok=True)

shutil.copy2(URLS, backup_dir / "urls.py")
if API_FILE.exists():
    shutil.copy2(API_FILE, backup_dir / "api_xml.py")

print(f"Backup cod creat: {backup_dir}")

API_CONTENT = 'from datetime import datetime\nfrom pathlib import Path\nimport secrets\nimport xml.etree.ElementTree as ET\n\nfrom django.conf import settings\nfrom django.http import HttpResponse\nfrom django.shortcuts import get_object_or_404\nfrom django.views.decorators.csrf import csrf_exempt\n\nfrom .models import User, Task, Reminder, Mesaj, AuditLog, RaportSupervizor\n\nTOKEN_FILE = Path(settings.BASE_DIR) / ".api_read_token"\n\n\ndef _read_token():\n    try:\n        return TOKEN_FILE.read_text(encoding="utf-8").strip()\n    except Exception:\n        return ""\n\n\ndef _authorized(request):\n    configured = _read_token()\n    if not configured:\n        return False\n\n    header = request.headers.get("Authorization", "")\n    if not header.startswith("Bearer "):\n        return False\n\n    supplied = header[7:].strip()\n    return secrets.compare_digest(configured, supplied)\n\n\ndef _text(parent, tag, value):\n    node = ET.SubElement(parent, tag)\n\n    if value is None:\n        node.set("nil", "true")\n        return node\n\n    if isinstance(value, bool):\n        node.text = "true" if value else "false"\n    elif isinstance(value, datetime):\n        node.text = value.isoformat(timespec="seconds")\n    else:\n        node.text = str(value)\n\n    return node\n\n\ndef _xml_response(root, status=200):\n    try:\n        ET.indent(root, space="  ")\n    except AttributeError:\n        pass\n\n    body = ET.tostring(root, encoding="utf-8", xml_declaration=True)\n    response = HttpResponse(\n        body,\n        status=status,\n        content_type="application/xml; charset=utf-8",\n    )\n\n    response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"\n    response["Pragma"] = "no-cache"\n    response["Expires"] = "0"\n    response["X-Data-Source"] = "live-sqlite"\n    response["X-Read-Only"] = "true"\n    return response\n\n\ndef _error(code, message, status):\n    root = ET.Element("error")\n    _text(root, "code", code)\n    _text(root, "message", message)\n    return _xml_response(root, status=status)\n\n\ndef read_only_api(view_func):\n    @csrf_exempt\n    def wrapper(request, *args, **kwargs):\n        if request.method != "GET":\n            response = _error(\n                "method_not_allowed",\n                "This API is read-only. Only GET is permitted.",\n                405,\n            )\n            response["Allow"] = "GET"\n            return response\n\n        if not _authorized(request):\n            return _error(\n                "unauthorized",\n                "Missing or invalid read-only API token.",\n                401,\n            )\n\n        return view_func(request, *args, **kwargs)\n\n    return wrapper\n\n\ndef _base_root(name):\n    root = ET.Element(name)\n    root.set("generatedAt", datetime.now().isoformat(timespec="seconds"))\n    root.set("source", "live")\n    root.set("readOnly", "true")\n    return root\n\n\ndef _serialize_user(parent, user):\n    node = ET.SubElement(parent, "user")\n    _text(node, "id", user.id)\n    _text(node, "username", user.username)\n    _text(node, "firstName", user.first_name)\n    _text(node, "lastName", user.last_name)\n    _text(node, "email", user.email)\n    _text(node, "role", getattr(user, "role", ""))\n    _text(node, "isActive", user.is_active)\n    _text(node, "isStaff", user.is_staff)\n    _text(node, "isSuperuser", user.is_superuser)\n    _text(node, "lastLogin", user.last_login)\n    _text(node, "dateJoined", user.date_joined)\n    return node\n\n\ndef _serialize_task(parent, task):\n    node = ET.SubElement(parent, "task")\n    _text(node, "id", task.id)\n    _text(node, "title", task.titlu)\n    _text(node, "description", task.descriere)\n    _text(node, "location", task.locatie)\n    _text(node, "action", task.actiune)\n    _text(node, "observations", task.observatii)\n    _text(node, "completionReport", task.raport_finalizare)\n\n    _text(node, "status", task.status)\n    _text(node, "priority", task.prioritate)\n    _text(node, "notificationSent", task.notificare_trimisa)\n\n    _text(node, "createdAt", task.data_crearii)\n    _text(node, "deadline", task.deadline)\n    _text(node, "startedAt", task.data_inceperii)\n    _text(node, "completedAt", task.data_finalizarii)\n\n    _text(node, "startLatitude", task.latitudine_inceput)\n    _text(node, "startLongitude", task.longitudine_inceput)\n\n    _text(node, "lastPauseStartedAt", task.ultima_incepere_pauza)\n    _text(node, "pausedSeconds", task.suma_pauze_secunde)\n    _text(node, "workedSeconds", task.timp_lucrat_secunde)\n\n    creator = ET.SubElement(node, "createdBy")\n    if task.creat_de_id:\n        _text(creator, "id", task.creat_de_id)\n        _text(creator, "username", task.creat_de.username)\n        _text(creator, "role", getattr(task.creat_de, "role", ""))\n\n    supervisor = ET.SubElement(node, "supervisor")\n    if task.supervizor_id:\n        _text(supervisor, "id", task.supervizor_id)\n        _text(supervisor, "username", task.supervizor.username)\n        _text(supervisor, "role", getattr(task.supervizor, "role", ""))\n\n    assigned = ET.SubElement(node, "assignedUsers")\n    for user in task.atribuit_catre.all().order_by("id"):\n        user_node = ET.SubElement(assigned, "user")\n        _text(user_node, "id", user.id)\n        _text(user_node, "username", user.username)\n        _text(user_node, "firstName", user.first_name)\n        _text(user_node, "lastName", user.last_name)\n        _text(user_node, "role", getattr(user, "role", ""))\n\n    return node\n\n\ndef _serialize_reminder(parent, reminder):\n    node = ET.SubElement(parent, "reminder")\n    _text(node, "id", reminder.id)\n    _text(node, "title", reminder.titlu)\n    _text(node, "details", reminder.detalii)\n    _text(node, "reminderDate", reminder.data_reminder)\n    _text(node, "createdAt", reminder.creat_la)\n    _text(node, "completed", getattr(reminder, "finalizat", False))\n    _text(node, "completedAt", getattr(reminder, "data_finalizarii", None))\n\n    creator = ET.SubElement(node, "createdBy")\n    _text(creator, "id", reminder.user_id)\n    _text(creator, "username", reminder.user.username)\n    _text(creator, "role", getattr(reminder.user, "role", ""))\n    return node\n\n\ndef _serialize_message(parent, message):\n    node = ET.SubElement(parent, "message")\n    _text(node, "id", message.id)\n    _text(node, "content", message.continut)\n    _text(node, "sentAt", message.data_trimitere)\n    _text(node, "read", message.citit)\n\n    sender = ET.SubElement(node, "sender")\n    _text(sender, "id", message.expeditor_id)\n    _text(sender, "username", message.expeditor.username)\n\n    recipient = ET.SubElement(node, "recipient")\n    _text(recipient, "id", message.destinatar_id)\n    _text(recipient, "username", message.destinatar.username)\n    return node\n\n\ndef _serialize_audit(parent, item):\n    node = ET.SubElement(parent, "auditEntry")\n    _text(node, "id", item.id)\n    _text(node, "ipAddress", item.ip_address)\n    _text(node, "action", item.actiune)\n    _text(node, "dateTime", item.data_ora)\n\n    user_node = ET.SubElement(node, "user")\n    if item.user_id:\n        _text(user_node, "id", item.user_id)\n        _text(user_node, "username", item.user.username)\n        _text(user_node, "role", getattr(item.user, "role", ""))\n    return node\n\n\ndef _serialize_report(parent, report):\n    node = ET.SubElement(parent, "report")\n    _text(node, "id", report.id)\n    _text(node, "reportDate", report.data_raportului)\n    _text(node, "workDone", report.ce_s_a_facut)\n    _text(node, "workNotDone", report.ce_nu_s_a_facut)\n    _text(node, "workStatus", report.stare_lucrare)\n\n    task_node = ET.SubElement(node, "task")\n    _text(task_node, "id", report.task_id)\n    _text(task_node, "title", report.task.titlu)\n    _text(task_node, "location", report.task.locatie)\n    _text(task_node, "status", report.task.status)\n\n    supervisor = ET.SubElement(node, "supervisor")\n    _text(supervisor, "id", report.supervizor_id)\n    _text(supervisor, "username", report.supervizor.username)\n\n    evaluated = ET.SubElement(node, "evaluatedEmployee")\n    if report.angajat_evaluat_id:\n        _text(evaluated, "id", report.angajat_evaluat_id)\n        _text(evaluated, "username", report.angajat_evaluat.username)\n        _text(evaluated, "role", getattr(report.angajat_evaluat, "role", ""))\n\n    return node\n\n\ndef _users_queryset():\n    return User.objects.all().order_by("id")\n\n\ndef _tasks_queryset():\n    return (\n        Task.objects\n        .select_related("creat_de", "supervizor")\n        .prefetch_related("atribuit_catre")\n        .all()\n        .order_by("id")\n    )\n\n\ndef _reminders_queryset():\n    return Reminder.objects.select_related("user").all().order_by("id")\n\n\ndef _messages_queryset():\n    return (\n        Mesaj.objects\n        .select_related("expeditor", "destinatar")\n        .all()\n        .order_by("id")\n    )\n\n\ndef _audit_queryset():\n    return AuditLog.objects.select_related("user").all().order_by("id")\n\n\ndef _reports_queryset():\n    return (\n        RaportSupervizor.objects\n        .select_related("task", "supervizor", "angajat_evaluat")\n        .all()\n        .order_by("id")\n    )\n\n\n@read_only_api\ndef api_live(request):\n    root = _base_root("taskManager")\n\n    users_node = ET.SubElement(root, "users")\n    for user in _users_queryset():\n        _serialize_user(users_node, user)\n\n    tasks_node = ET.SubElement(root, "tasks")\n    for task in _tasks_queryset():\n        _serialize_task(tasks_node, task)\n\n    history_node = ET.SubElement(root, "history")\n    for task in _tasks_queryset().filter(status="finalizat"):\n        _serialize_task(history_node, task)\n\n    reminders_node = ET.SubElement(root, "reminders")\n    for reminder in _reminders_queryset():\n        _serialize_reminder(reminders_node, reminder)\n\n    messages_node = ET.SubElement(root, "messages")\n    for message in _messages_queryset():\n        _serialize_message(messages_node, message)\n\n    reports_node = ET.SubElement(root, "reports")\n    for report in _reports_queryset():\n        _serialize_report(reports_node, report)\n\n    audit_node = ET.SubElement(root, "audit")\n    for item in _audit_queryset():\n        _serialize_audit(audit_node, item)\n\n    counts = ET.SubElement(root, "counts")\n    _text(counts, "users", User.objects.count())\n    _text(counts, "tasks", Task.objects.count())\n    _text(counts, "completedTasks", Task.objects.filter(status="finalizat").count())\n    _text(counts, "reminders", Reminder.objects.count())\n    _text(counts, "messages", Mesaj.objects.count())\n    _text(counts, "reports", RaportSupervizor.objects.count())\n    _text(counts, "auditEntries", AuditLog.objects.count())\n\n    return _xml_response(root)\n\n\n@read_only_api\ndef api_users(request):\n    root = _base_root("users")\n    for user in _users_queryset():\n        _serialize_user(root, user)\n    return _xml_response(root)\n\n\n@read_only_api\ndef api_user_detail(request, user_id):\n    user = get_object_or_404(User, id=user_id)\n    root = _base_root("userDetail")\n    _serialize_user(root, user)\n    return _xml_response(root)\n\n\n@read_only_api\ndef api_tasks(request):\n    root = _base_root("tasks")\n    for task in _tasks_queryset():\n        _serialize_task(root, task)\n    return _xml_response(root)\n\n\n@read_only_api\ndef api_task_detail(request, task_id):\n    task = get_object_or_404(_tasks_queryset(), id=task_id)\n    root = _base_root("taskDetail")\n    _serialize_task(root, task)\n    return _xml_response(root)\n\n\n@read_only_api\ndef api_history(request):\n    root = _base_root("history")\n    for task in _tasks_queryset().filter(status="finalizat"):\n        _serialize_task(root, task)\n    return _xml_response(root)\n\n\n@read_only_api\ndef api_reminders(request):\n    root = _base_root("reminders")\n    for reminder in _reminders_queryset():\n        _serialize_reminder(root, reminder)\n    return _xml_response(root)\n\n\n@read_only_api\ndef api_reminder_detail(request, reminder_id):\n    reminder = get_object_or_404(_reminders_queryset(), id=reminder_id)\n    root = _base_root("reminderDetail")\n    _serialize_reminder(root, reminder)\n    return _xml_response(root)\n\n\n@read_only_api\ndef api_messages(request):\n    root = _base_root("messages")\n    for message in _messages_queryset():\n        _serialize_message(root, message)\n    return _xml_response(root)\n\n\n@read_only_api\ndef api_reports(request):\n    root = _base_root("reports")\n    for report in _reports_queryset():\n        _serialize_report(root, report)\n    return _xml_response(root)\n\n\n@read_only_api\ndef api_report_detail(request, report_id):\n    report = get_object_or_404(_reports_queryset(), id=report_id)\n    root = _base_root("reportDetail")\n    _serialize_report(root, report)\n    return _xml_response(root)\n\n\n@read_only_api\ndef api_audit(request):\n    root = _base_root("audit")\n    for item in _audit_queryset():\n        _serialize_audit(root, item)\n    return _xml_response(root)\n'
ROUTES = "    # --- API XML READ-ONLY / LIVE ---\n    path('api/xml/live/', api_xml.api_live, name='api_xml_live'),\n    path('api/xml/database/', api_xml.api_live, name='api_xml_database'),\n    path('api/xml/users/', api_xml.api_users, name='api_xml_users'),\n    path('api/xml/users/<int:user_id>/', api_xml.api_user_detail, name='api_xml_user_detail'),\n    path('api/xml/tasks/', api_xml.api_tasks, name='api_xml_tasks'),\n    path('api/xml/tasks/<int:task_id>/', api_xml.api_task_detail, name='api_xml_task_detail'),\n    path('api/xml/history/', api_xml.api_history, name='api_xml_history'),\n    path('api/xml/reminders/', api_xml.api_reminders, name='api_xml_reminders'),\n    path('api/xml/reminders/<int:reminder_id>/', api_xml.api_reminder_detail, name='api_xml_reminder_detail'),\n    path('api/xml/messages/', api_xml.api_messages, name='api_xml_messages'),\n    path('api/xml/reports/', api_xml.api_reports, name='api_xml_reports'),\n    path('api/xml/reports/<int:report_id>/', api_xml.api_report_detail, name='api_xml_report_detail'),\n    path('api/xml/audit/', api_xml.api_audit, name='api_xml_audit'),\n"

API_FILE.write_text(API_CONTENT, encoding="utf-8")
print("OK: core/api_xml.py")

urls = URLS.read_text(encoding="utf-8")

if "from . import api_xml" not in urls:
    marker = "from . import views\n"
    if marker in urls:
        urls = urls.replace(marker, marker + "from . import api_xml\n", 1)
    else:
        urls = "from . import api_xml\n" + urls

route_marker = "# --- API XML READ-ONLY / LIVE ---"
if route_marker not in urls:
    last = urls.rfind("]")
    if last == -1:
        print("EROARE: Nu pot modifica automat core/urls.py")
        sys.exit(1)

    urls = urls[:last] + ROUTES + urls[last:]

URLS.write_text(urls, encoding="utf-8")
print("OK: core/urls.py")

if not TOKEN_FILE.exists() or not TOKEN_FILE.read_text(encoding="utf-8").strip():
    token = secrets.token_urlsafe(48)
    TOKEN_FILE.write_text(token + "\n", encoding="utf-8")
    print("Token API read-only creat.")
else:
    token = TOKEN_FILE.read_text(encoding="utf-8").strip()
    print("Token API existent pastrat.")

existing = GITIGNORE.read_text(encoding="utf-8") if GITIGNORE.exists() else ""
if ".api_read_token" not in existing:
    if existing and not existing.endswith("\n"):
        existing += "\n"
    existing += ".api_read_token\n"
    GITIGNORE.write_text(existing, encoding="utf-8")
    print("OK: .api_read_token adaugat in .gitignore")

print()
print("=" * 72)
print("API XML READ-ONLY INSTALAT")
print("=" * 72)
print("TOKEN:")
print(token)
print()
print("LIVE COMPLET:")
print("  /api/xml/live/")
print("  /api/xml/database/")
print()
print("SEPARAT:")
print("  /api/xml/users/")
print("  /api/xml/users/<id>/")
print("  /api/xml/tasks/")
print("  /api/xml/tasks/<id>/")
print("  /api/xml/history/")
print("  /api/xml/reminders/")
print("  /api/xml/reminders/<id>/")
print("  /api/xml/messages/")
print("  /api/xml/reports/")
print("  /api/xml/reports/<id>/")
print("  /api/xml/audit/")
print()
print("Token salvat in:", TOKEN_FILE)
print("=" * 72)
