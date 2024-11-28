from django.contrib import admin
from django.urls import reverse
from django.urls.exceptions import NoReverseMatch

from ukgrantmaking.admin.cleaningstatus import CleaningStatusAdmin
from ukgrantmaking.admin.financial_year import FinancialYearAdmin
from ukgrantmaking.admin.funder import FunderAdmin, FunderTagAdmin
from ukgrantmaking.admin.funder_financial_year import FunderFinancialYearAdmin
from ukgrantmaking.admin.funder_year import FunderYearAdmin
from ukgrantmaking.admin.grants import (
    CurrencyConverterAdmin,
    GrantAdmin,
    GrantRecipientAdmin,
    GrantRecipientYearAdmin,
)
from ukgrantmaking.models.cleaningstatus import CleaningStatus
from ukgrantmaking.models.financial_years import FinancialYear
from ukgrantmaking.models.funder import Funder, FunderTag
from ukgrantmaking.models.funder_financial_year import FunderFinancialYear
from ukgrantmaking.models.funder_year import FunderYear
from ukgrantmaking.models.grant import (
    CurrencyConverter,
    Grant,
    GrantRecipient,
    GrantRecipientYear,
)


class UKGrantmakingAdminSite(admin.AdminSite):
    site_title = "UK Grantmaking"
    site_header = "UK Grantmaking Data Cleaning"

    def __init__(self, *args, **kwargs):
        super(UKGrantmakingAdminSite, self).__init__(*args, **kwargs)
        self._registry.update(admin.site._registry)

        for model, model_admin in self._registry.items():
            model_admin.admin_site = self

    def _build_app_dict(self, request, label=None):
        app_dict = super(UKGrantmakingAdminSite, self)._build_app_dict(
            request, label=label
        )

        for app_label in app_dict:
            models = []
            for model in app_dict[app_label]["models"]:
                app_label = model["model"]._meta.app_label
                model_name = model["model"]._meta.model_name
                model["upload_url"] = None
                if model["add_url"] is not None:
                    try:
                        model["upload_url"] = reverse(
                            f"admin:{app_label}_{model_name}_upload"
                        )
                    except NoReverseMatch:
                        pass
                models.append(model)
            app_dict[app_label]["models"] = models
        return app_dict


admin_site = UKGrantmakingAdminSite(name="myadmin")
admin_site.register(Funder, FunderAdmin)
admin_site.register(FunderTag, FunderTagAdmin)
admin_site.register(FunderYear, FunderYearAdmin)
admin_site.register(FunderFinancialYear, FunderFinancialYearAdmin)

admin_site.register(Grant, GrantAdmin)
admin_site.register(CurrencyConverter, CurrencyConverterAdmin)
admin_site.register(GrantRecipient, GrantRecipientAdmin)
admin_site.register(GrantRecipientYear, GrantRecipientYearAdmin)

admin_site.register(FinancialYear, FinancialYearAdmin)

admin_site.register(CleaningStatus, CleaningStatusAdmin)
