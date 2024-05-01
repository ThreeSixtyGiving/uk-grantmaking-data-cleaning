from django.contrib import admin
from django.urls import reverse
from django.urls.exceptions import NoReverseMatch

from ukgrantmaking.admin.funders import FunderAdmin, FunderTagAdmin, FunderYearAdmin
from ukgrantmaking.admin.grants import CurrencyConverterAdmin, GrantAdmin
from ukgrantmaking.models import (
    CurrencyConverter,
    Funder,
    FunderTag,
    FunderYear,
    Grant,
)


class UKGrantmakingAdminSite(admin.AdminSite):
    site_title = "UK Grantmaking"
    site_header = "UK Grantmaking Data Cleaning"

    def __init__(self, *args, **kwargs):
        super(UKGrantmakingAdminSite, self).__init__(*args, **kwargs)
        print(self.index_template)
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

admin_site.register(Grant, GrantAdmin)
admin_site.register(CurrencyConverter, CurrencyConverterAdmin)
