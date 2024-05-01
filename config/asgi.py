import os

from datasette.app import Datasette
from django.core.asgi import get_asgi_application
from django.db import connections

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# adding datasette from https://til.simonwillison.net/django/datasette-django
datasette_application = Datasette(
    [
        str(db["NAME"])
        for db in connections.databases.values()
        if db["ENGINE"] == "django.db.backends.sqlite3"
    ],
    settings={
        "base_url": "/datasette/",
    },
    metadata={
        "plugins": {
            "datasette-auth-existing-cookies": {
                "api_url": "/user-from-cookies",
            }
        },
        "allow": {
            "id": "*",
        },
        "databases": {
            "db": {
                "tables": {
                    "auth_user": {"allow": False},
                    "auth_group": {"allow": False},
                    "auth_group_permissions": {"allow": False},
                    "auth_permission": {"allow": False},
                    "auth_user_groups": {"allow": False},
                    "auth_user_user_permissions": {"allow": False},
                    "cache_table": {"allow": False},
                    "csvimport_csvimport": {"allow": False},
                    "csvimport_importmodel": {"allow": False},
                    "django_admin_log": {"allow": False},
                    "django_content_type": {"allow": False},
                    "django_migrations": {"allow": False},
                    "django_session": {"allow": False},
                    "django_sql_dashboard_dashboard": {"allow": False},
                    "django_sql_dashboard_dashboardquery": {"allow": False},
                    "sqlite_sequence": {"allow": False},
                }
            }
        },
    },
).app()
django_application = get_asgi_application()


async def application(scope, receive, send):
    if scope["type"] == "http" and scope.get("path").startswith("/datasette/"):
        await datasette_application(scope, receive, send)
    else:
        await django_application(scope, receive, send)
