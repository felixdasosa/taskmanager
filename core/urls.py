from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView
from . import views
from . import api_xml

urlpatterns = [
    # Logare / Logout
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Utilizatori
    path('adauga-utilizator/', views.adauga_utilizator, name='adauga_utilizator'),
    path('utilizatori/', views.lista_utilizatori, name='lista_utilizatori'),
    path('utilizatori/reseteaza/<int:user_id>/', views.reseteaza_parola, name='reseteaza_parola'),
    path('utilizatori/sterge/<int:user_id>/', views.sterge_utilizator, name='sterge_utilizator'),
    path('profil/', views.profil_utilizator, name='profil'),
    
    # Task-uri
    path('creeaza-task/', views.creeaza_task, name='creeaza_task'),
    path('taskuri/', views.lista_taskuri, name='lista_taskuri'),
    path('task/incepe/<int:task_id>/', views.incepe_task, name='incepe_task'),
    path('task/finalizeaza/<int:task_id>/', views.finalizeaza_task, name='finalizeaza_task'),
    path('editeaza-task/<int:task_id>/', views.editeaza_task, name='editeaza_task'),
    path('sterge-task/<int:task_id>/', views.sterge_task, name='sterge_task'),
    path('pauza-task/<int:task_id>/', views.pauza_task, name='pauza_task'),
    path('relua-task/<int:task_id>/', views.relua_task, name='relua_task'),
    
    # Istoric, Audit și Export
    path('istoric/', views.istoric_taskuri, name='istoric_taskuri'),
    path('audit/', views.vizualizare_audit, name='vizualizare_audit'),
    path('export-raport-excel/', views.export_raport_excel, name='export_raport_excel'),
    
    # Mesaje și Notificări
    path('mesaje/', views.lista_mesaje, name='lista_mesaje'),
    path('webpush/', include('webpush.urls')),
    
    # Reminders (Noile rute)
    path('reminders/', views.lista_reminders, name='lista_reminders'),
    path('reminders/sterge/<int:reminder_id>/', views.sterge_reminder, name='sterge_reminder'),
    path('reminders/finalizeaza/<int:reminder_id>/', views.finalizeaza_reminder, name='finalizeaza_reminder'),
    path('reminders/reactiveaza/<int:reminder_id>/', views.reactiveaza_reminder, name='reactiveaza_reminder'),
    path('task/<int:task_id>/adauga-raport/', views.adauga_raport_supervizor, name='adauga_raport_supervizor'),
    path('raport/sterge/<int:raport_id>/', views.sterge_raport, name='sterge_raport'),
    path('manifest.json', TemplateView.as_view(template_name='core/manifest.json', content_type='application/json'), name='manifest'),
    path('sw.js', TemplateView.as_view(template_name='core/sw.js', content_type='application/javascript'), name='sw'),
path('task/<int:task_id>/gps_silent/', views.actualizeaza_gps_silent, name='actualizeaza_gps_silent'),
    # --- API XML READ-ONLY / LIVE ---
    path('api/xml/live/', api_xml.api_live, name='api_xml_live'),
    path('api/xml/database/', api_xml.api_live, name='api_xml_database'),
    path('api/xml/users/', api_xml.api_users, name='api_xml_users'),
    path('api/xml/users/<int:user_id>/', api_xml.api_user_detail, name='api_xml_user_detail'),
    path('api/xml/tasks/', api_xml.api_tasks, name='api_xml_tasks'),
    path('api/xml/tasks/<int:task_id>/', api_xml.api_task_detail, name='api_xml_task_detail'),
    path('api/xml/history/', api_xml.api_history, name='api_xml_history'),
    path('api/xml/reminders/', api_xml.api_reminders, name='api_xml_reminders'),
    path('api/xml/reminders/<int:reminder_id>/', api_xml.api_reminder_detail, name='api_xml_reminder_detail'),
    path('api/xml/messages/', api_xml.api_messages, name='api_xml_messages'),
    path('api/xml/reports/', api_xml.api_reports, name='api_xml_reports'),
    path('api/xml/reports/<int:report_id>/', api_xml.api_report_detail, name='api_xml_report_detail'),
    path('api/xml/audit/', api_xml.api_audit, name='api_xml_audit'),
]