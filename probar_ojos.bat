@echo off
rem Doble clic: prueba que el Arduino responde (los ojos hacen "feliz" y despues "sorpresa").
chcp 65001 >nul
cd /d "%~dp0"
set PYTHONUTF8=1
.venv\Scripts\python.exe serie.py "E 7" "espera 3" "E 1" "espera 3" "D"
pause
