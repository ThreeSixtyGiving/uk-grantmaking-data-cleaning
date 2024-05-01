from django.contrib import admin

from ukgrantmaking.admin.funders import FunderAdmin, FunderTagAdmin, FunderYearAdmin
from ukgrantmaking.admin.grants import CurrencyConverterAdmin, GrantAdmin
from ukgrantmaking.models import (
    CurrencyConverter,
    Funder,
    FunderTag,
    FunderYear,
    Grant,
)

admin.site.site_title = "UK Grantmaking"
admin.site.site_header = "UK Grantmaking Data Cleaning"

admin.site.register(Funder, FunderAdmin)
admin.site.register(FunderTag, FunderTagAdmin)
admin.site.register(FunderYear, FunderYearAdmin)

admin.site.register(Grant, GrantAdmin)
admin.site.register(CurrencyConverter, CurrencyConverterAdmin)
