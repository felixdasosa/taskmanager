@echo off
cd /d "%~dp0"

echo.
echo ======================================================
echo  INSTALARE API XML READ-ONLY - DATE LIVE
echo ======================================================
echo.

python instaleaza_api_xml_live.py
if errorlevel 1 (
    echo.
    echo EROARE la instalarea API-ului.
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
echo ======================================================
echo  INSTALARE TERMINATA
echo ======================================================
echo.
echo Reporneste aplicatia Django.
echo Tokenul este salvat in .api_read_token
echo.
pause
