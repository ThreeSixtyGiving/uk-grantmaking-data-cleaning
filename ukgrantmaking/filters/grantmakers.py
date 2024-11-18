import django_filters
from django.db import models

from ukgrantmaking.models import Funder
from ukgrantmaking.models.funder import FunderSegment


class NewOrderingFilter(django_filters.OrderingFilter):
    def get_ordering_value(self, param):
        descending = param.startswith("-")
        param = param[1:] if descending else param
        field_name = self.param_map.get(param, param)

        if descending:
            return models.F(field_name).desc(nulls_last=True)

        return models.F(field_name).asc(nulls_last=True)


class GrantmakerFilter(django_filters.FilterSet):
    latest_year__checked = django_filters.BooleanFilter(
        field_name="latest_year__checked"
    )
    segment = django_filters.MultipleChoiceFilter(
        field_name="segment", choices=FunderSegment.choices
    )
    search = django_filters.CharFilter(
        field_name="name", lookup_expr="icontains", label="Search"
    )

    latest_year__income__gt = django_filters.NumberFilter(
        field_name="latest_year__income", lookup_expr="gt"
    )
    latest_year__income__lt = django_filters.NumberFilter(
        field_name="latest_year__income", lookup_expr="lt"
    )
    latest_year__spending__gt = django_filters.NumberFilter(
        field_name="latest_year__spending", lookup_expr="gt"
    )
    latest_year__spending__lt = django_filters.NumberFilter(
        field_name="latest_year__spending", lookup_expr="lt"
    )
    latest_year__spending_grant_making__gt = django_filters.NumberFilter(
        field_name="latest_year__spending_grant_making", lookup_expr="gt"
    )
    latest_year__spending_grant_making__lt = django_filters.NumberFilter(
        field_name="latest_year__spending_grant_making", lookup_expr="lt"
    )
    latest_year__funds_endowment__gt = django_filters.NumberFilter(
        field_name="latest_year__funds_endowment", lookup_expr="gt"
    )
    latest_year__funds_endowment__lt = django_filters.NumberFilter(
        field_name="latest_year__funds_endowment", lookup_expr="lt"
    )

    o = NewOrderingFilter(
        # tuple-mapping retains order
        fields=(
            ("name", "name"),
            ("latest_year__income", "latest_year__income"),
            ("latest_year__spending", "latest_year__spending"),
            (
                "latest_year__spending_grant_making",
                "latest_year__spending_grant_making",
            ),
            (
                "latest_year__spending_grant_making_individuals",
                "latest_year__spending_grant_making_individuals",
            ),
            (
                "latest_year__spending_grant_making_institutions",
                "latest_year__spending_grant_making_institutions",
            ),
            ("latest_year__funds", "latest_year__funds"),
            ("latest_year__funds_endowment", "latest_year__funds_endowment"),
            ("latest_year__employees", "latest_year__employees"),
        ),
        # labels do not need to retain order
        field_labels={
            "name": "Organisation name",
            "latest_year__income": "Income",
            "latest_year__spending": "Spending",
            "latest_year__spending_grant_making": "Grantmaking",
            "latest_year__spending_grant_making_individuals": "Grantmaking - Individuals",
            "latest_year__spending_grant_making_institutions": "Grantmaking - Institutions",
            "latest_year__funds": "Funds",
            "latest_year__funds_endowment": "Endowment funds",
            "latest_year__employees": "Employees",
        },
    )

    class Meta:
        model = Funder
        fields = [
            "search",
            "included",
            "active",
            "segment",
            "tags",
            "makes_grants_to_individuals",
        ]
        filter_overrides = {
            models.GeneratedField: {
                "filter_class": django_filters.CharFilter,
            },
        }
