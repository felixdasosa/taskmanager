from pathlib import Path
import shutil
import sys
from datetime import datetime

ROOT = Path(__file__).resolve().parent
models_path = ROOT / "core" / "models.py"
views_path = ROOT / "core" / "views.py"
urls_path = ROOT / "core" / "urls.py"
template_path = ROOT / "core" / "templates" / "core" / "reminders.html"

required = [models_path, views_path, urls_path, template_path]
missing = [str(p) for p in required if not p.exists()]
if missing:
    print("EROARE: Nu gasesc fisierele necesare:")
    for p in missing:
        print(" -", p)
    print("\nPune acest script in acelasi folder cu manage.py.")
    sys.exit(1)

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_dir = ROOT / f"backup_remindere_finalizate_{stamp}"
backup_dir.mkdir(exist_ok=True)

for src in required:
    rel = src.relative_to(ROOT)
    dst = backup_dir / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)

print(f"Backup creat: {backup_dir}")

models = models_path.read_text(encoding="utf-8")
start = models.find("class Reminder(models.Model):")
if start == -1:
    print("EROARE: Nu am gasit modelul Reminder.")
    sys.exit(1)
end = models.find("\nclass ", start + 1)
if end == -1:
    end = len(models)

block = models[start:end]
if "finalizat = models.BooleanField" not in block:
    anchor = "    creat_la = models.DateTimeField(auto_now_add=True)\n"
    if anchor not in block:
        print("EROARE: Nu am gasit campul creat_la in Reminder.")
        sys.exit(1)
    block = block.replace(
        anchor,
        anchor +
        "    finalizat = models.BooleanField(default=False)\n"
        "    data_finalizarii = models.DateTimeField(null=True, blank=True)\n"
    )
    models = models[:start] + block + models[end:]
    models_path.write_text(models, encoding="utf-8")
print("OK: core/models.py")

views = views_path.read_text(encoding="utf-8")
start = views.find("@login_required\ndef lista_reminders(request):")
end = views.find("\n@login_required\ndef sterge_reminder", start)
if start == -1 or end == -1:
    print("EROARE: Nu am gasit lista_reminders/sterge_reminder.")
    sys.exit(1)

new_views = '@login_required\ndef lista_reminders(request):\n    if request.user.role not in [\'superadmin\', \'manager\']:\n        return redirect(\'dashboard\')\n\n    reminder_editat = None\n    status_lista = request.GET.get(\'status\', \'active\')\n    afiseaza_finalizate = status_lista == \'finalizate\'\n\n    if request.method == \'POST\':\n        reminder_id = request.POST.get(\'reminder_id\')\n\n        if reminder_id:\n            reminder_editat = get_object_or_404(\n                Reminder,\n                id=reminder_id,\n                user=request.user\n            )\n            form = ReminderForm(request.POST, instance=reminder_editat)\n        else:\n            form = ReminderForm(request.POST)\n\n        if form.is_valid():\n            reminder = form.save(commit=False)\n            reminder.user = request.user\n            reminder.save()\n\n            if reminder_id:\n                messages.success(request, "Reminderul a fost actualizat cu succes.")\n            else:\n                messages.success(request, "Reminderul a fost adaugat cu succes.")\n\n            return redirect(\'lista_reminders\')\n    else:\n        reminder_id = request.GET.get(\'edit\')\n\n        if reminder_id:\n            reminder_editat = get_object_or_404(\n                Reminder,\n                id=reminder_id,\n                user=request.user\n            )\n            form = ReminderForm(instance=reminder_editat)\n        else:\n            form = ReminderForm()\n\n    baza = Reminder.objects.filter(user=request.user)\n\n    if afiseaza_finalizate:\n        reminders = baza.filter(finalizat=True).order_by(\'-data_finalizarii\', \'-data_reminder\')\n    else:\n        reminders = baza.filter(finalizat=False).order_by(\'data_reminder\')\n\n    return render(request, \'core/reminders.html\', {\n        \'reminders\': reminders,\n        \'form\': form,\n        \'reminder_editat\': reminder_editat,\n        \'afiseaza_finalizate\': afiseaza_finalizate,\n        \'nr_active\': baza.filter(finalizat=False).count(),\n        \'nr_finalizate\': baza.filter(finalizat=True).count(),\n    })\n\n\n@login_required\ndef finalizeaza_reminder(request, reminder_id):\n    if request.user.role not in [\'superadmin\', \'manager\']:\n        return redirect(\'dashboard\')\n\n    reminder = get_object_or_404(Reminder, id=reminder_id, user=request.user)\n\n    if request.method == \'POST\':\n        reminder.finalizat = True\n        reminder.data_finalizarii = timezone.now()\n        reminder.save(update_fields=[\'finalizat\', \'data_finalizarii\'])\n        messages.success(request, f"Reminderul \'{reminder.titlu}\' a fost marcat ca finalizat.")\n\n    return redirect(\'lista_reminders\')\n\n\n@login_required\ndef reactiveaza_reminder(request, reminder_id):\n    if request.user.role not in [\'superadmin\', \'manager\']:\n        return redirect(\'dashboard\')\n\n    reminder = get_object_or_404(Reminder, id=reminder_id, user=request.user)\n\n    if request.method == \'POST\':\n        reminder.finalizat = False\n        reminder.data_finalizarii = None\n        reminder.save(update_fields=[\'finalizat\', \'data_finalizarii\'])\n        messages.success(request, f"Reminderul \'{reminder.titlu}\' a fost reactivat.")\n\n    return redirect(\'lista_reminders\')\n'
views = views[:start] + new_views + views[end:]
views_path.write_text(views, encoding="utf-8")
print("OK: core/views.py")

urls = urls_path.read_text(encoding="utf-8")
if "name='finalizeaza_reminder'" not in urls:
    anchor = "    path('reminders/sterge/<int:reminder_id>/', views.sterge_reminder, name='sterge_reminder'),\n"
    if anchor not in urls:
        print("EROARE: Nu am gasit ruta sterge_reminder.")
        sys.exit(1)

    extra = (
        "    path('reminders/finalizeaza/<int:reminder_id>/', views.finalizeaza_reminder, name='finalizeaza_reminder'),\n"
        "    path('reminders/reactiveaza/<int:reminder_id>/', views.reactiveaza_reminder, name='reactiveaza_reminder'),\n"
    )
    urls = urls.replace(anchor, anchor + extra)
    urls_path.write_text(urls, encoding="utf-8")
print("OK: core/urls.py")

template = '{% extends \'core/dashboard.html\' %}\n\n{% block content %}\n<div class="container-fluid mt-4">\n    <div class="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-4">\n        <h2 class="mb-0">🔔 Remindere</h2>\n        <div class="d-flex gap-2">\n            {% if afiseaza_finalizate %}\n                <a href="{% url \'lista_reminders\' %}" class="btn btn-primary">\n                    ← Remindere active\n                    <span class="badge bg-light text-primary ms-1">{{ nr_active }}</span>\n                </a>\n            {% else %}\n                <a href="{% url \'lista_reminders\' %}?status=finalizate" class="btn btn-outline-success">\n                    ✅ Remindere finalizate\n                    <span class="badge bg-success ms-1">{{ nr_finalizate }}</span>\n                </a>\n            {% endif %}\n        </div>\n    </div>\n\n    {% if messages %}\n        {% for message in messages %}\n            <div class="alert alert-{{ message.tags|default:\'success\' }} alert-dismissible fade show" role="alert">\n                {{ message }}\n                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>\n            </div>\n        {% endfor %}\n    {% endif %}\n\n    {% if not afiseaza_finalizate or reminder_editat %}\n    <div class="card shadow-sm mb-4">\n        <div class="card-body">\n            <h5 class="card-title mb-3">\n                {% if reminder_editat %}✏️ Editează reminderul{% else %}Adaugă un memento nou{% endif %}\n            </h5>\n\n            <form method="POST">\n                {% csrf_token %}\n                {% if reminder_editat %}\n                    <input type="hidden" name="reminder_id" value="{{ reminder_editat.id }}">\n                {% endif %}\n\n                <div class="row">\n                    <div class="col-md-4 mb-3">\n                        <label class="form-label">Titlu</label>\n                        {{ form.titlu }}\n                    </div>\n                    <div class="col-md-4 mb-3">\n                        <label class="form-label">Data și Ora</label>\n                        {{ form.data_reminder }}\n                    </div>\n                    <div class="col-md-12 mb-3">\n                        <label class="form-label">Detalii</label>\n                        {{ form.detalii }}\n                    </div>\n                </div>\n\n                <button type="submit" class="btn btn-primary">\n                    {% if reminder_editat %}Salvează modificările{% else %}Salvează Memento{% endif %}\n                </button>\n\n                {% if reminder_editat %}\n                    <a href="{% url \'lista_reminders\' %}{% if afiseaza_finalizate %}?status=finalizate{% endif %}"\n                       class="btn btn-outline-secondary ms-2">Anulează</a>\n                {% endif %}\n            </form>\n        </div>\n    </div>\n    {% endif %}\n\n    <div class="card shadow-sm">\n        <div class="card-body">\n            <h5 class="card-title mb-3">\n                {% if afiseaza_finalizate %}✅ Remindere finalizate{% else %}Remindere active{% endif %}\n            </h5>\n\n            <div class="table-responsive">\n                <table class="table table-hover align-middle">\n                    <thead class="table-light">\n                        <tr>\n                            <th>Titlu</th>\n                            <th>Data reminder</th>\n                            {% if afiseaza_finalizate %}<th>Finalizat la</th>{% endif %}\n                            <th>Detalii</th>\n                            <th class="text-center">Acțiune</th>\n                        </tr>\n                    </thead>\n                    <tbody>\n                        {% for r in reminders %}\n                        <tr>\n                            <td class="fw-bold">\n                                {% if afiseaza_finalizate %}\n                                    <span class="text-decoration-line-through text-muted">{{ r.titlu }}</span>\n                                {% else %}\n                                    {{ r.titlu }}\n                                {% endif %}\n                            </td>\n                            <td>{{ r.data_reminder|date:"d M Y, H:i" }}</td>\n                            {% if afiseaza_finalizate %}\n                                <td>{% if r.data_finalizarii %}{{ r.data_finalizarii|date:"d M Y, H:i" }}{% else %}-{% endif %}</td>\n                            {% endif %}\n                            <td>{{ r.detalii }}</td>\n                            <td class="text-center text-nowrap">\n                                {% if afiseaza_finalizate %}\n                                    <form method="POST" action="{% url \'reactiveaza_reminder\' r.id %}" class="d-inline">\n                                        {% csrf_token %}\n                                        <button type="submit" class="btn btn-outline-warning btn-sm me-1">↩ Reactivează</button>\n                                    </form>\n                                    <a href="{% url \'lista_reminders\' %}?status=finalizate&edit={{ r.id }}"\n                                       class="btn btn-outline-primary btn-sm me-1">✏️ Editează</a>\n                                {% else %}\n                                    <form method="POST" action="{% url \'finalizeaza_reminder\' r.id %}" class="d-inline"\n                                          onsubmit="return confirm(\'Marchezi acest reminder ca finalizat?\');">\n                                        {% csrf_token %}\n                                        <button type="submit" class="btn btn-success btn-sm me-1">✓ Finalizează</button>\n                                    </form>\n                                    <a href="{% url \'lista_reminders\' %}?edit={{ r.id }}"\n                                       class="btn btn-outline-primary btn-sm me-1">✏️ Editează</a>\n                                {% endif %}\n\n                                <a href="{% url \'sterge_reminder\' r.id %}" class="btn btn-outline-danger btn-sm"\n                                   onclick="return confirm(\'Sigur vrei să ștergi definitiv acest reminder?\');">Șterge</a>\n                            </td>\n                        </tr>\n                        {% empty %}\n                        <tr>\n                            <td colspan="{% if afiseaza_finalizate %}5{% else %}4{% endif %}"\n                                class="text-center text-muted py-4">\n                                {% if afiseaza_finalizate %}Nu ai niciun reminder finalizat.{% else %}Nu ai niciun reminder activ.{% endif %}\n                            </td>\n                        </tr>\n                        {% endfor %}\n                    </tbody>\n                </table>\n            </div>\n        </div>\n    </div>\n</div>\n{% endblock %}\n'
template_path.write_text(template, encoding="utf-8")
print("OK: core/templates/core/reminders.html")
print("\nModificarile au fost aplicate. Continua cu makemigrations si migrate.")
