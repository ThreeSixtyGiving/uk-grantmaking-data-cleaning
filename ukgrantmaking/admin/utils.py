from dataclasses import dataclass

from django.contrib import admin, messages
from django.contrib.admin.utils import (
    quote,
)
from django.contrib.admin.views.main import ChangeList
from django.urls import reverse


@dataclass
class Action:
    label: str
    field: str
    values: tuple
    set_null: bool = False


def add_admin_actions(action_fields: list[Action]):
    def make_action_function(field_label, field, value):
        def action_function(modeladmin, request, queryset):
            queryset.update(**{field: value})
            modeladmin.message_user(
                request,
                f"{queryset.count()} grants {field_label} have been set as `{value}`.",
                messages.SUCCESS,
            )

        return action_function

    actions = {}

    for action in action_fields:
        if action.set_null:
            actions[f"set_as_{action.field}_null"] = (
                make_action_function(action.label, action.field, None),
                f"set_as_{action.field}_null",
                f"Set {action.label} to None",
            )
        for choice in action.values.choices:
            action_name = f"set_as_{action.field}_{choice[0].lower()}"
            if action_name not in actions:
                actions[action_name] = (
                    make_action_function(action.label, action.field, choice[0]),
                    action_name,
                    f"Set {action.label} to {choice[1]}",
                )

    return actions


class AdminViewChangeList(ChangeList):
    def url_for_result(self, result):
        pk = getattr(result, "pk")
        return reverse(
            "admin:%s_%s_change" % (self.opts.app_label, self.opts.model_name),
            args=(quote(pk),),
            current_app=self.model_admin.admin_site.name,
        )


class DBViewAdmin(admin.ModelAdmin):
    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_changelist(self, request, **kwargs):
        """
        Return the ChangeList class for use on the changelist page.
        """
        return AdminViewChangeList
