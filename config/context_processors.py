from dataclasses import dataclass
from typing import Optional

from django.urls import reverse

from ukgrantmaking.models.financial_years import FinancialYear
from ukgrantmaking.views.docs import get_docs


@dataclass
class SidebarItem:
    title: str
    icon: Optional[str] = None
    active: bool = False
    view: Optional[str] = None
    count: Optional[int] = None
    children: Optional[list["SidebarItem"]] = None
    query: Optional[str] = None
    url_args: Optional[list] = None

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
            if self.url_args:
                url = reverse(self.view, args=self.url_args)
            else:
                url = reverse(self.view)
            if self.query:
                url += f"?{self.query}"
            return url
        return "#"


def sidebar(request):
    options = {
        "sidebar": [
            SidebarItem(title="Home", view=("index")),
        ],
        "sidebar_settings": [],
    }
    if request.user.is_authenticated:
        docs = get_docs()
        options["sidebar"].extend(
            [
                SidebarItem(
                    title="Grantmakers",
                    view="grantmakers:index",
                    query="included=true&o=-latest_year__scaling",
                    children=[
                        SidebarItem(
                            title="Tasks",
                            view="grantmakers:task_index",
                        ),
                        SidebarItem(
                            title="Admin",
                            view="admin:ukgrantmaking_funder_changelist",
                        ),
                    ],
                ),
                SidebarItem(
                    title="Grants", view="admin:ukgrantmaking_grant_changelist"
                ),
                SidebarItem(
                    title="Help",
                    view="docs:index",
                    children=[
                        SidebarItem(
                            title=doc.title,
                            view="docs:detail",
                            url_args=[doc.doc_path],
                        )
                        for doc in docs
                    ],
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


def current_fy(request):
    if request.user.is_authenticated:
        return {"current_fy": FinancialYear.objects.current()}
    return {"current_fy": None}
