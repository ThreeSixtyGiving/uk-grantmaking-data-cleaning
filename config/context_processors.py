from dataclasses import dataclass
from typing import Optional

from django.urls import reverse


@dataclass
class SidebarItem:
    title: str
    icon: Optional[str] = None
    active: bool = False
    view: Optional[str] = None
    count: Optional[int] = None
    children: Optional[list["SidebarItem"]] = None

    @property
    def classes(self):
        classes = ["sidebar-item"]
        if self.active:
            classes.append("active")
        if self.children:
            classes.append("has-children")
        return " ".join(classes)

    @property
    def url(self):
        if self.view:
            return reverse(self.view)
        return "#"


def sidebar(request):
    options = {
        "sidebar": [
            SidebarItem(title="Home", view=("index")),
        ],
        "sidebar_settings": [],
    }
    if request.user.is_authenticated:
        options["sidebar"].extend(
            [
                SidebarItem(title="Grantmakers", view="grantmakers:index"),
                SidebarItem(
                    title="Grants", view="admin:ukgrantmaking_grant_changelist"
                ),
            ]
        )
        options["sidebar_settings"].extend(
            [
                SidebarItem(title="Admin", view=("admin:index")),
                SidebarItem(title="Logout", view=("logout")),
            ]
        )
    else:
        options["sidebar_settings"].append(SidebarItem(title="Login", view=("login")))

    for item in options["sidebar"]:
        if request.resolver_match.url_name == item.view:
            item.active = True

    for item in options["sidebar_settings"]:
        if request.resolver_match.url_name == item.view:
            item.active = True

    return options
