from adminsortable2.admin import SortableAdminBase, SortableTabularInline
from django.contrib import admin

from ukgrantmaking.models.cleaningstatus import CleaningStatusQuery


class CleaningStatusQueryAdminInline(SortableTabularInline):
    model = CleaningStatusQuery
    fields = (
        "field",
        "operator",
        "comparison",
        "value",
        "active",
        "order",
    )
    ordering = ("order",)


class CleaningStatusAdmin(SortableAdminBase, admin.ModelAdmin):
    list_display = (
        "name",
        "type",
        "n",
        "sort_by",
        "sort_order",
    )
    inlines = (CleaningStatusQueryAdminInline,)
