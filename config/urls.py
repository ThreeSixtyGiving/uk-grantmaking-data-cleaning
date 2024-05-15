"""uk-grantmaking-data URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib.auth import views as auth_views
from django.urls import include, path

from ukgrantmaking.admin import admin_site
from ukgrantmaking.views import check_cookies as check_cookies_view
from ukgrantmaking.views import export_funders_excel as export_funders_view
from ukgrantmaking.views import export_grants_excel as export_grants_view
from ukgrantmaking.views import financial_year as financial_year_view
from ukgrantmaking.views import financial_year_grants_view
from ukgrantmaking.views import index as index_view
from ukgrantmaking.views import table_creator as table_creator_view

urlpatterns = [
    path(
        "",
        index_view,
        name="index",
    ),
    path(
        "table-creator/",
        table_creator_view,
        name="table_creator",
    ),
    path(
        "financial-year/<str:fy>/grantmakers.xlsx",
        financial_year_view,
        {"filetype": "xlsx"},
        name="financial_year_xlsx",
    ),
    path(
        "financial-year/<str:fy>/grantmakers",
        financial_year_view,
        name="financial_year",
    ),
    path(
        "financial-year/<str:fy>/grants.xlsx",
        financial_year_grants_view,
        {"filetype": "xlsx"},
        name="financial_year_grants_xlsx",
    ),
    path(
        "financial-year/<str:fy>/grants",
        financial_year_grants_view,
        name="financial_year_grants",
    ),
    path("admin/", admin_site.urls),
    path(
        "accounts/login/",
        auth_views.LoginView.as_view(template_name="registration/login.html.j2"),
        name="login",
    ),
    path(
        "accounts/logout/",
        auth_views.LogoutView.as_view(template_name="registration/logged_out.html.j2"),
        name="logout",
    ),
    path("__debug__/", include("debug_toolbar.urls")),
    path("export/funders.xlsx", export_funders_view),
    path("export/grants.xlsx", export_grants_view),
    path("user-from-cookies", check_cookies_view),
]
