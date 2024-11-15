from django.contrib import admin

from ukgrantmaking.models.cleaningstatus import CleaningStatusQuery


class CleaningStatusQueryAdminInline(admin.TabularInline):
    model = CleaningStatusQuery
    fields = (
        "field",
        "comparison",
        "value",
        "active",
    )


class CleaningStatusAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "type",
        "n",
        "sort_by",
        "sort_order",
    )
    inlines = (CleaningStatusQueryAdminInline,)
