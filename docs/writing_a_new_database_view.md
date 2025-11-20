# Writing a new data view

As well as the main table models described in [data_model](data_model.md) it is also possible to
create database views that show the data in different ways.

To create a new view, follow these steps:

## 1. Create a new model

Create the model in the `ukgrantmaking/models/views/` directory.

```python
from django.db import models
from django_db_views.db_view import DBView

from ukgrantmaking.models.funder_utils import FunderCategory, FunderSegment


class FundersView(DBView):
    field_one = models.CharField(max_length=50, primary_key=True)
    field_two = models.CharField(max_length=255)

    view_definition = {
        "django.db.backends.postgresql": """
        SELECT field_one, field_two
        FROM existing_table
        """
    }

    class Meta:
        managed = False  # Managed must be set to False!
        # db_table = "ukgrantmaking_funders_view" - can be set if needed
```

The model should have a `view_defition` dictionary, where the `django.db.backends.postgresql` key
has the SQL SELECT query used to create the view. Any changes to this statement will be picked up
in migrations.

The fields defined on the model must match those defined in the SQL statement.

The view model should then be imported into `ukgrantmaking/models/__init__.py` so that it can be
found by django.

## 2. Create a migration

To generate a migration you need to run `python manage.py makeviewmigrations` (note that views
won't be picked up if you just run the normal `python manage.py makemigrations` command).

If using the field outside of the django site then you can make a note of the name used for
the view, which appears in the migration file.

## 3. Run the migration

Run the normal `python manage.py migrate` command to add the view to the database.

## 4. [Optional] Add the view to the read only database user

If you would like the view to be used outside of django, you'll need to make sure that
the readonly database user has access to it. To do this, run an SQL command on the database:

```sql
GRANT SELECT ON "new_view_name" TO readonlyuser;
```

## 5. [Optional] Add an admin page for the view

**Important**: for this to work, a unique primary key should be defined on the model
(by adding `primary_key=True` to a field).

Create a new admin class in `ukgrantmaking/admin/` directory. The class should inherit
from `ukgrantmaking.admin.utils.DBViewAdmin`:

```python
from ukgrantmaking.admin.utils import DBViewAdmin

class FundersViewAdmin(DBViewAdmin):
    list_display = ("field_one", "field_two")
```

You can use the same options as a normal `ModelAdmin` view. Note that the view admin
is automatically set up to be readonly, so you can't change, add or delete items.

Make sure the admin class is added to `ukgrantmaking/admin/__init__.py` as follows:

```python
from ukgrantmaking.models.views.funders import FundersView
from ukgrantmaking.admin.funder import FundersViewAdmin

admin_site.register(FundersView, FunderViewAdmin)
```
