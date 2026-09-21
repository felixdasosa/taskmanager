@echo off
cd /d "%~dp0"

echo.
echo ================================================
echo  INSTALARE REMINDERE FINALIZATE
echo ================================================
echo.

python adauga_remindere_finalizate.py
if errorlevel 1 (
    echo.
    echo EROARE la modificarea fisierelor.
    pause
    exit /b 1
)

echo.
echo [1/3] Creez migratia...
python manage.py makemigrations core
if errorlevel 1 (
    echo.
    echo EROARE la makemigrations.
    pause
    exit /b 1
)

echo.
echo [2/3] Aplic migratia...
python manage.py migrate
if errorlevel 1 (
    echo.
    echo EROARE la migrate.
    pause
    exit /b 1
)

echo.
echo [3/3] Verific proiectul...
python manage.py check
if errorlevel 1 (
    echo.
    echo EROARE la verificarea Django.
    pause
    exit /b 1
)

echo.
echo ================================================
echo  GATA - REMINDERE FINALIZATE INSTALATE
echo ================================================
echo.
echo Reporneste aplicatia si intra la Remindere.
pause
