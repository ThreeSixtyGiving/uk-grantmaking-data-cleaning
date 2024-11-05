import django_filters
from django.db import models

from ukgrantmaking.models import Funder
from ukgrantmaking.models.funder import FunderSegment


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

    o = django_filters.OrderingFilter(
        # tuple-mapping retains order
        fields=(
            ("name", "name"),
            ("latest_grantmaking", "latest_grantmaking"),
        ),
        # labels do not need to retain order
        field_labels={
            "name": "Organisation name",
            "latest_grantmaking": "Grantmaking",
        },
    )

    class Meta:
        model = Funder
        fields = [
            "search",
            "included",
            "latest_year__checked",
            "segment",
            "tags",
            "makes_grants_to_individuals",
            # "org_id_schema",
            "latest_year__financial_year",
            # "latest_grantmaking",
        ]
        filter_overrides = {
            models.GeneratedField: {
                "filter_class": django_filters.CharFilter,
            },
        }
