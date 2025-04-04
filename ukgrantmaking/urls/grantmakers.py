from django.urls import path

from ukgrantmaking.views.grantmakers import (
    detail,
    htmx_edit_funder,
    htmx_edit_funderyear,
    htmx_edit_note,
    htmx_tags_edit,
    index,
    task_detail,
    task_index,
    upload_csv,
)

app_name = "grantmakers"

urlpatterns = [
    path(
        "",
        index,
        name="index",
    ),
    path(
        "upload",
        upload_csv,
        name="upload_csv",
    ),
    path(
        "tasks/",
        task_index,
        name="task_index",
    ),
    path(
        "tasks/<int:task_id>",
        task_detail,
        name="task_detail",
    ),
    path(
        "tasks/<int:task_id>.csv",
        task_detail,
        name="task_detail_csv",
        kwargs={"filetype": "csv"},
    ),
    path(
        "funder/<path:org_id>/funderyear/<int:funderyear_id>",
        htmx_edit_funderyear,
        name="edit_funderyear",
    ),
    path(
        "funder/<path:org_id>/note/<int:note_id>",
        htmx_edit_note,
        name="edit_note",
    ),
    path(
        "funder/<path:org_id>/change_status",
        htmx_edit_funder,
        name="change_status",
    ),
    path(
        "funder/<path:org_id>/tags",
        htmx_tags_edit,
        name="edit_tags",
    ),
    path(
        "funder/<path:org_id>/note",
        htmx_edit_note,
        name="add_note",
    ),
    path(
        "funder/<path:org_id>/funderyear",
        htmx_edit_funderyear,
        name="add_funderyear",
    ),
    path(
        "funder/<path:org_id>/",
        detail,
        name="detail",
    ),
]
