from django.db import models


class FunderSegment(models.TextChoices):
    DONOR_ADVISED_FUND = "Donor Advised Fund", "Donor Advised Fund"
    WELLCOME_TRUST = "Wellcome Trust", "Wellcome Trust"
    CHARITY = "Charity", "Charity"
    LOTTERY_DISTRIBUTOR = "Lottery Distributor", "Lottery Distributor"
    ARMS_LENGTH_BODY = "Arms Length Body", "Arms Length Body"
    CORPORATE_FOUNDATION = "Corporate Foundation", "Corporate Foundation"
    FAMILY_FOUNDATION = "Family Foundation", "Family Foundation"
    FUNDRAISING_GRANTMAKER = "Fundraising Grantmaker", "Fundraising Grantmaker"
    GENERAL_GRANTMAKER = "General grantmaker", "General grantmaker"
    MEMBER_TRADE_FUNDED = "Member/Trade Funded", "Member/Trade Funded"
    NHS_HOSPITAL_FOUNDATION = "NHS/Hospital Foundation", "NHS/Hospital Foundation"
    GOVERNMENT_LOTTERY_ENDOWED = (
        "Government/Lottery Endowed",
        "Government/Lottery Endowed",
    )
    SMALL_GRANTMAKER = "Small grantmaker", "Small grantmaker"
    COMMUNITY_FOUNDATION = "Community Foundation", "Community Foundation"
    LOCAL = "Local", "Local"
    CENTRAL = "Central", "Central"
    DEVOLVED = "Devolved", "Devolved"

    @property
    def category(self):
        return FUNDER_CATEGORIES[self]


class FunderCategory(models.TextChoices):
    GRANTMAKER = "Grantmaker", "Grantmaker"
    LOTTERY = "Lottery", "Lottery"
    CHARITY = "Charity", "Charity"
    GOVERNMENT = "Government", "Government"
    OTHER = "Other", "Other"


FUNDER_CATEGORIES = {
    FunderSegment.COMMUNITY_FOUNDATION: FunderCategory.GRANTMAKER,
    FunderSegment.CORPORATE_FOUNDATION: FunderCategory.GRANTMAKER,
    FunderSegment.FAMILY_FOUNDATION: FunderCategory.GRANTMAKER,
    FunderSegment.FUNDRAISING_GRANTMAKER: FunderCategory.GRANTMAKER,
    FunderSegment.GENERAL_GRANTMAKER: FunderCategory.GRANTMAKER,
    FunderSegment.GOVERNMENT_LOTTERY_ENDOWED: FunderCategory.GRANTMAKER,
    FunderSegment.MEMBER_TRADE_FUNDED: FunderCategory.GRANTMAKER,
    FunderSegment.SMALL_GRANTMAKER: FunderCategory.GRANTMAKER,
    FunderSegment.WELLCOME_TRUST: FunderCategory.GRANTMAKER,
    FunderSegment.LOTTERY_DISTRIBUTOR: FunderCategory.LOTTERY,
    FunderSegment.CHARITY: FunderCategory.CHARITY,
    FunderSegment.NHS_HOSPITAL_FOUNDATION: FunderCategory.CHARITY,
    FunderSegment.LOCAL: FunderCategory.GOVERNMENT,
    FunderSegment.CENTRAL: FunderCategory.GOVERNMENT,
    FunderSegment.DEVOLVED: FunderCategory.GOVERNMENT,
    FunderSegment.ARMS_LENGTH_BODY: FunderCategory.GOVERNMENT,
    FunderSegment.DONOR_ADVISED_FUND: FunderCategory.OTHER,
}


class RecordStatus(models.TextChoices):
    UNCHECKED = "Unchecked", "Unchecked"
    CHECKED = "Checked", "Checked"
    NEW = "New", "New"
