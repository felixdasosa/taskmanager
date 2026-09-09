from pathlib import Path
import shutil
import sys
from datetime import datetime

ROOT = Path(__file__).resolve().parent

forms_path = ROOT / "core" / "forms.py"
views_path = ROOT / "core" / "views.py"
template_path = ROOT / "core" / "templates" / "core" / "reminders.html"

required = [forms_path, views_path, template_path]
missing = [str(p) for p in required if not p.exists()]
if missing:
    print("EROARE: Nu gasesc fisierele necesare:")
    for p in missing:
        print(" -", p)
    print("\nPune acest script in acelasi folder cu manage.py.")
    sys.exit(1)

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_dir = ROOT / f"backup_edit_reminder_{stamp}"
backup_dir.mkdir(exist_ok=True)

for src in required:
    rel = src.relative_to(ROOT)
    dst = backup_dir / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)

print(f"Backup creat: {backup_dir}")

forms = forms_path.read_text(encoding="utf-8")
start = forms.find("class ReminderForm(forms.ModelForm):")
end = forms.find("class RaportSupervizorForm(forms.ModelForm):", start)

if start == -1 or end == -1:
    print("EROARE: Nu am gasit blocul ReminderForm in core/forms.py")
    sys.exit(1)

new_form = '''class ReminderForm(forms.ModelForm):
    class Meta:
        model = Reminder
        fields = ['titlu', 'detalii', 'data_reminder']
        widgets = {
            'titlu': forms.TextInput(attrs={'class': 'form-control'}),
            'detalii': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'data_reminder': forms.DateTimeInput(
                attrs={'type': 'datetime-local', 'class': 'form-control'},
                format='%Y-%m-%dT%H:%M'
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['data_reminder'].input_formats = ['%Y-%m-%dT%H:%M']


'''
forms = forms[:start] + new_form + forms[end:]
forms_path.write_text(forms, encoding="utf-8")
print("OK: core/forms.py")

views = views_path.read_text(encoding="utf-8")
start = views.find("@login_required\ndef lista_reminders(request):")
end = views.find("\n@login_required\ndef sterge_reminder", start)

if start == -1 or end == -1:
    print("EROARE: Nu am gasit functia lista_reminders in core/views.py")
    sys.exit(1)

new_view = '''@login_required
def lista_reminders(request):
    if request.user.role not in ['superadmin', 'manager']:
        return redirect('dashboard')

    reminder_editat = None

    if request.method == 'POST':
        reminder_id = request.POST.get('reminder_id')

        if reminder_id:
            reminder_editat = get_object_or_404(
                Reminder,
                id=reminder_id,
                user=request.user
            )
            form = ReminderForm(request.POST, instance=reminder_editat)
        else:
            form = ReminderForm(request.POST)

        if form.is_valid():
            reminder = form.save(commit=False)
            reminder.user = request.user
            reminder.save()

            if reminder_id:
                messages.success(request, "Reminderul a fost actualizat cu succes.")
            else:
                messages.success(request, "Reminderul a fost adaugat cu succes.")

            return redirect('lista_reminders')
    else:
        reminder_id = request.GET.get('edit')

        if reminder_id:
            reminder_editat = get_object_or_404(
                Reminder,
                id=reminder_id,
                user=request.user
            )
            form = ReminderForm(instance=reminder_editat)
        else:
            form = ReminderForm()

    reminders = Reminder.objects.filter(
        user=request.user
    ).order_by('data_reminder')

    return render(request, 'core/reminders.html', {
        'reminders': reminders,
        'form': form,
        'reminder_editat': reminder_editat,
    })
'''
views = views[:start] + new_view + views[end:]
views_path.write_text(views, encoding="utf-8")
print("OK: core/views.py")

template = '''{% extends 'core/dashboard.html' %}

{% block content %}
<div class="container-fluid mt-4">
    <h2 class="mb-4">🔔 Remindere</h2>

    {% if messages %}
        {% for message in messages %}
            <div class="alert alert-{{ message.tags|default:'success' }} alert-dismissible fade show" role="alert">
                {{ message }}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        {% endfor %}
    {% endif %}

    <div class="card shadow-sm mb-4">
        <div class="card-body">
            <h5 class="card-title mb-3">
                {% if reminder_editat %}
                    ✏️ Editează reminderul
                {% else %}
                    Adaugă un memento nou
                {% endif %}
            </h5>

            <form method="POST">
                {% csrf_token %}

                {% if reminder_editat %}
                    <input type="hidden" name="reminder_id" value="{{ reminder_editat.id }}">
                {% endif %}

                <div class="row">
                    <div class="col-md-4 mb-3">
                        <label class="form-label">Titlu</label>
                        {{ form.titlu }}
                    </div>

                    <div class="col-md-4 mb-3">
                        <label class="form-label">Data și Ora</label>
                        {{ form.data_reminder }}
                    </div>

                    <div class="col-md-12 mb-3">
                        <label class="form-label">Detalii</label>
                        {{ form.detalii }}
                    </div>
                </div>

                <button type="submit" class="btn btn-primary">
                    {% if reminder_editat %}
                        Salvează modificările
                    {% else %}
                        Salvează Memento
                    {% endif %}
                </button>

                {% if reminder_editat %}
                    <a href="{% url 'lista_reminders' %}" class="btn btn-outline-secondary ms-2">
                        Anulează
                    </a>
                {% endif %}
            </form>
        </div>
    </div>

    <div class="card shadow-sm">
        <div class="card-body">
            <h5 class="card-title mb-3">Lista mea de remindere</h5>

            <div class="table-responsive">
                <table class="table table-hover align-middle">
                    <thead class="table-light">
                        <tr>
                            <th>Titlu</th>
                            <th>Data</th>
                            <th>Detalii</th>
                            <th class="text-center">Acțiune</th>
                        </tr>
                    </thead>

                    <tbody>
                        {% for r in reminders %}
                        <tr {% if reminder_editat and reminder_editat.id == r.id %}class="table-primary"{% endif %}>
                            <td class="fw-bold">{{ r.titlu }}</td>
                            <td>{{ r.data_reminder|date:"d M Y, H:i" }}</td>
                            <td>{{ r.detalii }}</td>
                            <td class="text-center">
                                <a href="{% url 'lista_reminders' %}?edit={{ r.id }}"
                                   class="btn btn-outline-primary btn-sm me-1">
                                    ✏️ Editează
                                </a>

                                <a href="{% url 'sterge_reminder' r.id %}"
                                   class="btn btn-outline-danger btn-sm"
                                   onclick="return confirm('Sigur vrei să ștergi acest reminder?');">
                                    Șterge
                                </a>
                            </td>
                        </tr>
                        {% empty %}
                        <tr>
                            <td colspan="4" class="text-center text-muted py-4">
                                Nu ai niciun memento setat.
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</div>
{% endblock %}
'''
template_path.write_text(template, encoding="utf-8")
print("OK: core/templates/core/reminders.html")

print("\n==============================================")
print("MODIFICAREA A FOST APLICATA CU SUCCES.")
print("Nu este necesar makemigrations sau migrate.")
print("==============================================")
