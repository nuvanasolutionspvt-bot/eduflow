"""
Standalone database helper for EduFlow deployment.

This file does not change the Django project. It only reads the existing
models/migrations and can create the schema in an already-created MySQL/RDS
database by running Django migrations.

Usage from E:\Eduflow:
    python db.py show
    python db.py create-db
    python db.py check
    python db.py migrate
    python db.py createsuperuser

Before running against AWS RDS, set these in school_admin/.env or environment:
    SCHOOL_ADMIN_DB_NAME=your_database_name
    SCHOOL_ADMIN_DB_USER=your_rds_user
    SCHOOL_ADMIN_DB_PASSWORD=your_rds_password
    SCHOOL_ADMIN_DB_HOST=your-rds-endpoint.amazonaws.com
    SCHOOL_ADMIN_DB_PORT=3306
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = ROOT_DIR / "school_admin"


def setup_django():
    """Load the existing Django project without editing project files."""
    if not PROJECT_DIR.exists():
        raise RuntimeError(f"Project directory not found: {PROJECT_DIR}")

    sys.path.insert(0, str(PROJECT_DIR))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "school_admin.settings")

    import django

    django.setup()


def db_config():
    from django.conf import settings

    config = settings.DATABASES["default"].copy()
    config.pop("PASSWORD", None)
    return config


def print_connection():
    config = db_config()
    print("Database connection from current settings:")
    print(f"  ENGINE: {config.get('ENGINE')}")
    print(f"  NAME:   {config.get('NAME')}")
    print(f"  USER:   {config.get('USER')}")
    print(f"  HOST:   {config.get('HOST')}")
    print(f"  PORT:   {config.get('PORT')}")
    print()


def database_settings():
    from django.conf import settings

    database = settings.DATABASES["default"]
    return {
        "name": database.get("NAME"),
        "user": database.get("USER"),
        "password": database.get("PASSWORD"),
        "host": database.get("HOST"),
        "port": int(database.get("PORT") or 3306),
        "charset": database.get("OPTIONS", {}).get("charset", "utf8mb4"),
    }


def field_description(field):
    pieces = [field.__class__.__name__]

    max_length = getattr(field, "max_length", None)
    if max_length:
        pieces.append(f"max_length={max_length}")

    if getattr(field, "primary_key", False):
        pieces.append("primary_key")
    if getattr(field, "unique", False):
        pieces.append("unique")
    if getattr(field, "null", False):
        pieces.append("null")
    if getattr(field, "blank", False):
        pieces.append("blank")
    if getattr(field, "db_index", False):
        pieces.append("index")

    related_model = getattr(field, "related_model", None)
    if related_model:
        pieces.append(f"references={related_model._meta.db_table}")
        remote_field = getattr(field, "remote_field", None)
        if remote_field and remote_field.on_delete:
            pieces.append(f"on_delete={remote_field.on_delete.__name__}")

    return ", ".join(pieces)


def show_schema():
    from django.apps import apps

    print_connection()
    print("Schema from installed Django models:")

    for model in apps.get_models(include_auto_created=False):
        meta = model._meta
        print(f"\n[{meta.app_label}.{model.__name__}]")
        print(f"  table: {meta.db_table}")

        for field in meta.fields:
            print(f"  - {field.name}: {field_description(field)}")

        many_to_many = list(meta.many_to_many)
        if many_to_many:
            print("  many_to_many:")
            for field in many_to_many:
                through = field.remote_field.through._meta.db_table
                print(f"  - {field.name}: through={through}")

        constraints = list(meta.constraints)
        if constraints:
            print("  constraints:")
            for constraint in constraints:
                print(f"  - {constraint}")

        unique_together = meta.unique_together
        if unique_together:
            print(f"  unique_together: {unique_together}")


def check_database():
    from django.core.management import call_command

    print_connection()
    call_command("check")
    call_command("showmigrations")


def create_database():
    import pymysql

    config = database_settings()
    database_name = config["name"]
    if not database_name:
        raise RuntimeError("SCHOOL_ADMIN_DB_NAME is empty. Set it before creating the database.")

    print_connection()
    print(f"Creating database if missing: {database_name}")
    connection = pymysql.connect(
        host=config["host"],
        port=config["port"],
        user=config["user"],
        password=config["password"],
        charset=config["charset"],
        connect_timeout=15,
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{database_name}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        connection.commit()
    finally:
        connection.close()

    print("Database is ready. Now run: python db.py migrate")


def migrate_database():
    from django.core.management import call_command

    print_connection()
    print("Creating/updating schema using Django migrations...")
    call_command("migrate", interactive=False)
    print("Schema migration completed.")


def create_superuser():
    from django.core.management import call_command

    print_connection()
    call_command("createsuperuser")


def main():
    parser = argparse.ArgumentParser(description="EduFlow database deployment helper")
    parser.add_argument(
        "command",
        choices=["show", "create-db", "check", "migrate", "createsuperuser"],
        help="Action to run",
    )
    args = parser.parse_args()

    setup_django()

    if args.command == "show":
        show_schema()
    elif args.command == "create-db":
        create_database()
    elif args.command == "check":
        check_database()
    elif args.command == "migrate":
        migrate_database()
    elif args.command == "createsuperuser":
        create_superuser()


if __name__ == "__main__":
    main()
