@echo off
REM Start Celery Worker for BlueOlive on Windows
REM Uses 'solo' pool for Windows compatibility (no fork/multiprocessing)

cd /d "%~dp0core"

REM Start Celery worker with verbose logging
REM Solo pool: suitable for development on Windows
celery -A core worker --pool=solo --loglevel=info

REM To also run Celery Beat (scheduler), use:
REM celery -A core worker --beat --pool=solo --loglevel=info

REM Or in a separate terminal:
REM celery -A core beat --loglevel=info
