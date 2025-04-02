from dataclasses import dataclass
from typing import Optional

from django.db import models
from django.utils.translation import gettext_lazy as _


class FunderSegment(models.TextChoices):
    DONOR_ADVISED_FUND = "Donor Advised Fund", _("Donor Advised Fund")
    WELLCOME_TRUST = "Wellcome Trust", _("Wellcome Trust")
    CHARITY = "Charity", _("Charity")
    NATIONAL_LOTTERY_DISTRIBUTOR = (
        "National Lottery Distributor",
        _("National Lottery Distributor"),
    )
    ARMS_LENGTH_BODY = "Arms Length Body", _("Arms Length Body")
    CORPORATE_FOUNDATION = "Corporate Foundation", _("Corporate Foundation")
    FAMILY_FOUNDATION = "Family Foundation", _("Family Foundation")
    FUNDRAISING_GRANTMAKER = "Fundraising Grantmaker", _("Fundraising Grantmaker")
    GENERAL_FOUNDATION = "General Foundation", _("General Foundation")
    MEMBER_TRADE_FUNDED = "Member/Trade Funded", _("Member/Trade Funded")
    NHS_HOSPITAL_FOUNDATION = "NHS/Hospital Foundation", _("NHS/Hospital Foundation")
    GOVERNMENT_LOTTERY_ENDOWED = (
        "Government/Lottery Endowed",
        _("Government/Lottery Endowed"),
    )
    SMALL_GRANTMAKER = "Small Grantmaker", _("Small Grantmaker")
    COMMUNITY_FOUNDATION = "Community Foundation", _("Community Foundation")
    LOCAL = "Local", _("Local")
    CENTRAL = "Central", _("Central")
    DEVOLVED = "Devolved", _("Devolved")

    @property
    def category(self):
        return FUNDER_CATEGORIES[self]


class FunderCategory(models.TextChoices):
    TRUSTS_FOUNDATIONS = "Trusts and Foundations", _("Trusts and Foundations")
    NATIONAL_LOTTERY = "National Lottery", _("National Lottery")
    CHARITY = "Charity", _("Charity")
    GOVERNMENT = "Government", _("Government")
    OTHER = "Other", _("Other")


FUNDER_CATEGORIES = {
    FunderSegment.COMMUNITY_FOUNDATION: FunderCategory.TRUSTS_FOUNDATIONS,
    FunderSegment.CORPORATE_FOUNDATION: FunderCategory.TRUSTS_FOUNDATIONS,
    FunderSegment.FAMILY_FOUNDATION: FunderCategory.TRUSTS_FOUNDATIONS,
    FunderSegment.FUNDRAISING_GRANTMAKER: FunderCategory.TRUSTS_FOUNDATIONS,
    FunderSegment.GENERAL_FOUNDATION: FunderCategory.TRUSTS_FOUNDATIONS,
    FunderSegment.GOVERNMENT_LOTTERY_ENDOWED: FunderCategory.TRUSTS_FOUNDATIONS,
    FunderSegment.MEMBER_TRADE_FUNDED: FunderCategory.TRUSTS_FOUNDATIONS,
    FunderSegment.SMALL_GRANTMAKER: FunderCategory.TRUSTS_FOUNDATIONS,
    FunderSegment.WELLCOME_TRUST: FunderCategory.TRUSTS_FOUNDATIONS,
    FunderSegment.NATIONAL_LOTTERY_DISTRIBUTOR: FunderCategory.NATIONAL_LOTTERY,
    FunderSegment.CHARITY: FunderCategory.CHARITY,
    FunderSegment.NHS_HOSPITAL_FOUNDATION: FunderCategory.CHARITY,
    FunderSegment.LOCAL: FunderCategory.GOVERNMENT,
    FunderSegment.CENTRAL: FunderCategory.GOVERNMENT,
    FunderSegment.DEVOLVED: FunderCategory.GOVERNMENT,
    FunderSegment.ARMS_LENGTH_BODY: FunderCategory.GOVERNMENT,
    FunderSegment.DONOR_ADVISED_FUND: FunderCategory.OTHER,
}


class RecordStatus(models.TextChoices):
    UNCHECKED = "Unchecked", _("Unchecked")
    CHECKED = "Checked", _("Checked")
    NEW = "New", _("New")
    FOR_REVIEW = "For Review", _("For Review")


@dataclass
class EditableField:
    name: str
    label: str
    registered: Optional[models.Field] = None
    tsg: Optional[models.Field] = None
    manual: Optional[models.Field] = None

    @property
    def format_str(self) -> str:
        if self.name in [
            "employees",
            "employees_permanent",
            "employees_fixedterm",
            "employees_selfemployed",
        ]:
            return "{:,.0f}"
        return "£{:,.0f}"

    def set_field(self, field_name: str, field: models.Field):
        if field_name == "registered":
            self.registered = field
        elif field_name == "360Giving":
            self.tsg = field
        elif field_name == "manual":
            self.manual = field
