import django_filters
from django.db import models

from ukgrantmaking.models.funder import Funder, FunderSegment


class NewOrderingFilter(django_filters.OrderingFilter):
    def get_ordering_value(self, param):
        descending = param.startswith("-")
        param = param[1:] if descending else param
        field_name = self.param_map.get(param, param)

        if descending:
            return models.F(field_name).desc(nulls_last=True)

        return models.F(field_name).asc(nulls_last=True)


class GrantmakerFilter(django_filters.FilterSet):
    current_year__checked = django_filters.BooleanFilter(
        field_name="current_year__checked"
    )
    segment = django_filters.MultipleChoiceFilter(
        field_name="segment", choices=FunderSegment.choices
    )
    search = django_filters.CharFilter(
        field_name="name", lookup_expr="icontains", label="Search"
    )

    current_year__income__gt = django_filters.NumberFilter(
        field_name="current_year__income", lookup_expr="gt"
    )
    current_year__income__lt = django_filters.NumberFilter(
        field_name="current_year__income", lookup_expr="lt"
    )
    current_year__spending__gt = django_filters.NumberFilter(
        field_name="current_year__spending", lookup_expr="gt"
    )
    current_year__spending__lt = django_filters.NumberFilter(
        field_name="current_year__spending", lookup_expr="lt"
    )
    current_year__spending_grant_making__gt = django_filters.NumberFilter(
        field_name="current_year__spending_grant_making", lookup_expr="gt"
    )
    current_year__spending_grant_making__lt = django_filters.NumberFilter(
        field_name="current_year__spending_grant_making", lookup_expr="lt"
    )
    current_year__funds_endowment__gt = django_filters.NumberFilter(
        field_name="current_year__funds_endowment", lookup_expr="gt"
    )
    current_year__funds_endowment__lt = django_filters.NumberFilter(
        field_name="current_year__funds_endowment", lookup_expr="lt"
    )

    o = NewOrderingFilter(
        # tuple-mapping retains order
        fields=(
            ("name", "name"),
            ("latest_year__scaling", "latest_year__scaling"),
            ("current_year__scaling", "current_year__scaling"),
            ("current_year__income", "current_year__income"),
            ("current_year__spending", "current_year__spending"),
            (
                "current_year__spending_grant_making",
                "current_year__spending_grant_making",
            ),
            (
                "current_year__spending_grant_making_individuals",
                "current_year__spending_grant_making_individuals",
            ),
            (
                "current_year__spending_grant_making_institutions",
                "current_year__spending_grant_making_institutions",
            ),
            ("current_year__funds", "current_year__funds"),
            ("current_year__funds_endowment", "current_year__funds_endowment"),
            ("current_year__employees", "current_year__employees"),
        ),
        # labels do not need to retain order
        field_labels={
            "name": "Organisation name",
            "latest_year__scaling": "Grantmaker size (latest)",
            "current_year__scaling": "Grantmaker size",
            "current_year__income": "Income",
            "current_year__spending": "Spending",
            "current_year__spending_grant_making": "Grantmaking",
            "current_year__spending_grant_making_individuals": "Grantmaking - Individuals",
            "current_year__spending_grant_making_institutions": "Grantmaking - Institutions",
            "current_year__funds": "Funds",
            "current_year__funds_endowment": "Endowment funds",
            "current_year__employees": "Employees",
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
