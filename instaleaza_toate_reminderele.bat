@echo off
cd /d "%~dp0"

echo.
echo ================================================
echo  UPDATE - TOATE REMINDERELE PENTRU MANAGER
echo ================================================
echo.

python update_toate_reminderele.py
if errorlevel 1 (
    echo.
    echo EROARE la modificarea fisierelor.
    pause
    exit /b 1
)

echo.
echo Verific proiectul Django...
python manage.py check
if errorlevel 1 (
    echo.
    echo EROARE la verificarea Django.
    pause
    exit /b 1
)

echo.
echo ================================================
echo  GATA
echo ================================================
echo.
echo Reporneste aplicatia si intra la Remindere.
pause
