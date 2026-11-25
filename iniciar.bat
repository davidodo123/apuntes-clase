@echo off
rem Arranca la grabadora. Lo lanza la tarea programada "ApuntesClase" (o doble clic).
cd /d "%~dp0"
if not exist clases mkdir clases
set PYTHONIOENCODING=utf-8
".venv\Scripts\python.exe" servidor.py >> "clases\servidor.log" 2>> "clases\servidor.err.log"
