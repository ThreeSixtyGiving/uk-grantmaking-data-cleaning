from django.urls import path

from ukgrantmaking.views.grantmakers import (
    detail,
    htmx_edit_funderyear,
    htmx_edit_note,
    htmx_tags_edit,
    index,
)

app_name = "grantmakers"

urlpatterns = [
    path(
        "",
        index,
        name="index",
    ),
    path(
        "<str:org_id>/",
        detail,
        name="detail",
    ),
    path(
        "<str:org_id>/tags",
        htmx_tags_edit,
        name="edit_tags",
    ),
    path(
        "<str:org_id>/note",
        htmx_edit_note,
        name="add_note",
    ),
    path(
        "<str:org_id>/note/<int:note_id>",
        htmx_edit_note,
        name="edit_note",
    ),
    path(
        "<str:org_id>/funderyear",
        htmx_edit_funderyear,
        name="add_funderyear",
    ),
    path(
        "<str:org_id>/funderyear/<int:funderyear_id>",
        htmx_edit_funderyear,
        name="edit_funderyear",
    ),
]
