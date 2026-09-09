@echo off
cd /d "%~dp0"
echo.
echo Aplic modificarea pentru Edit Reminder...
echo.
python aplica_edit_reminder.py
if errorlevel 1 (
    echo.
    echo A aparut o eroare. Trimite-mi poza cu mesajul.
    pause
    exit /b 1
)

echo.
echo Verific proiectul Django...
python manage.py check
echo.
pause
