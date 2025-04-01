from dataclasses import dataclass

from django.contrib import messages


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
