import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "school_admin.settings")

from school_admin.wsgi import application as app
