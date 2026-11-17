@echo off
rem Doble clic: abre la pagina del robot en el navegador (http://localhost:8730). Desde ahi se enciende y apaga.
rem Cerrar esta ventana apaga la pagina.
chcp 65001 >nul
cd /d "%~dp0"
set PYTHONUTF8=1
if not exist .venv\Scripts\python.exe (
  echo Primero abre instalar_windows.bat
  pause
  exit /b 1
)
start "" /min cmd /c "timeout /t 2 >nul & start http://localhost:8730/#panel"
.venv\Scripts\python.exe -u servidor.py
pause
