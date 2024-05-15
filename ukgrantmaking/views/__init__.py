from io import BytesIO

import pandas as pd
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import render

from ukgrantmaking.models import (
    Funder,
    FunderTag,
    FunderYear,
    Grant,
)
from ukgrantmaking.views.grantmakers import financial_year
from ukgrantmaking.views.grants import financial_year_grants_view

__all__ = [
    "check_cookies",
    "export_all_data_excel",
    "export_funders_excel",
    "export_grants_excel",
    "index",
    "table_creator",
    "financial_year",
    "financial_year_grants_view",
]


@login_required
def index(request):
    return render(request, "index.html.j2")


def check_cookies(request):
    if request.user.is_superuser:
        return JsonResponse(
            {
                "id": request.user.id,
                "is_superuser": True,
                "username": request.user.username,
            }
        )
    return HttpResponseForbidden("You are not allowed to access this page")


def export_all_data_excel(models, filename):
    with pd.ExcelWriter(filename, engine="xlsxwriter") as writer:
        for model in models:
            print(model.__name__)
            df = pd.DataFrame.from_records(model.objects.all().values()).astype(str)
            print(f"{len(df)} records found")
            df.to_excel(writer, sheet_name=model.__name__)
            print(f"{len(df)} records written to excel")
    return filename


def export_funders_excel(request):
    models = [Funder, FunderYear, FunderTag]
    buffer = export_all_data_excel(models, BytesIO())
    buffer.seek(0)
    return HttpResponse(
        buffer.read(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


def export_grants_excel(request):
    models = [Grant]
    buffer = export_all_data_excel(models, BytesIO())
    buffer.seek(0)
    return HttpResponse(
        buffer.read(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


def table_creator(request):
    return render(request, "table_creator.html.j2")
