import os
import shutil
import socket
import threading
import time
from pathlib import Path

from waitress import serve
import webview

PROJECT_DIR = Path(__file__).resolve().parent
BUNDLED_DIR = Path(getattr(__import__('sys'), '_MEIPASS', PROJECT_DIR))
RUNTIME_DIR = Path(os.environ.get('LOCALAPPDATA', PROJECT_DIR)) / 'SchoolAdmin'
RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
RUNTIME_MEDIA_DIR = RUNTIME_DIR / 'media'
RUNTIME_MEDIA_DIR.mkdir(parents=True, exist_ok=True)


def copy_missing_tree(source_dir, destination_dir):
    if not source_dir.exists():
        return

    for source_path in source_dir.rglob('*'):
        relative_path = source_path.relative_to(source_dir)
        destination_path = destination_dir / relative_path

        if source_path.is_dir():
            destination_path.mkdir(parents=True, exist_ok=True)
            continue

        destination_path.parent.mkdir(parents=True, exist_ok=True)
        if not destination_path.exists():
            shutil.copy2(source_path, destination_path)

copy_missing_tree(BUNDLED_DIR / 'media', RUNTIME_MEDIA_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_admin.settings')
os.environ.setdefault('SCHOOL_ADMIN_BASE_DIR', str(BUNDLED_DIR))
os.environ.setdefault('SCHOOL_ADMIN_RUNTIME_DIR', str(RUNTIME_DIR))
os.environ.setdefault('SCHOOL_ADMIN_MEDIA_ROOT', str(RUNTIME_MEDIA_DIR))
os.environ.setdefault('SCHOOL_ADMIN_DB_HOST', 'localhost')
os.environ.setdefault('SCHOOL_ADMIN_DB_PORT', '3306')
os.environ.setdefault('SCHOOL_ADMIN_DB_USER', 'root')
os.environ.setdefault('SCHOOL_ADMIN_DB_PASSWORD', 'Qazwsx@123')
os.environ.setdefault('SCHOOL_ADMIN_DB_NAME', 'eduflow')

import django
from django.core.management import call_command


def apply_runtime_migrations():
    django.setup()
    call_command('migrate', interactive=False, verbosity=0)


apply_runtime_migrations()

from school_admin.wsgi import application
from django.contrib.staticfiles.handlers import StaticFilesHandler

HOST = '127.0.0.1'
PORT = 8000


def start_server():
    serve(StaticFilesHandler(application), host=HOST, port=PORT, threads=8)


def wait_for_server(timeout=15):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((HOST, PORT), timeout=1):
                return
        except OSError:
            time.sleep(0.2)
    raise RuntimeError('Django server did not start in time.')


threading.Thread(target=start_server, daemon=True).start()
wait_for_server()

webview.settings['ALLOW_DOWNLOADS'] = True

webview.create_window(
    "School Management System",
    f"http://{HOST}:{PORT}",
    width=1200,
    height=800
)

webview.start()
