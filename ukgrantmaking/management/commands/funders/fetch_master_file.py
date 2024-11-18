import djclick as click
from django.db import transaction
from openpyxl import load_workbook

from ukgrantmaking.models import Funder, FunderTag

TAG_LOOKUP = {
    "foundation_giving_trends": "Foundation Giving Trends",
    "360Giving_publisher": "360Giving Publisher",
    "snapshot_2023": "Snapshot 2023",
    "external: ACF_Current": "ACF Current",
    "external: ACF_Previous": "ACF Previous",
    "external: ACO": "ACO",
    "external: Community_Foundation": "Community Foundation",
    "external: Companies & Guilds": "Companies & Guilds",
    "external: Funders Forum for NI": "Funders Forum for NI",
    "external: Living Wage Funder": "Living Wage Funder",
    "external: London Funder": "London Funder",
    "external: UKCF": "UKCF",
    "dsc": "DSC",
    "ccew": "CCEW",
    "oscr": "OSCR",
    "ccni": "CCNI",
}


@click.command(deprecated=True)
@click.argument("file")
def master_list(file):
    click.secho("Opening {}".format(file), fg="green")

    wb = load_workbook(filename=file)

    funder_tags = {tag.tag: tag for tag in FunderTag.objects.all()}

    records = {
        "created": 0,
        "updated": 0,
    }

    with transaction.atomic():
        for sheet in wb:
            # iterate rows
            for table_name, table_range in sheet.tables.items():
                click.secho(
                    "Sheet: {} | Table: {}".format(sheet.title, table_name), fg="yellow"
                )

                header_row = None
                for row in sheet[table_range]:
                    if header_row is None:
                        header_row = [cell.value for cell in row]
                        continue
                    record = dict(zip(header_row, [cell.value for cell in row]))

                    # create or update Funder
                    funder, created = Funder.objects.get_or_create(
                        org_id=record["org_id"],
                        defaults={
                            "name_registered": record["name"],
                            "charity_number": record["charityNumber"],
                            "segment": record.get("segment_checked", record["segment"]),
                            "included": (
                                record["inclusion"] in ("non_charities", "included")
                            ),
                            "makes_grants_to_individuals": (
                                record["grants_to_individuals"] is not None
                            ),
                            "date_of_registration": record["dateRegistered"],
                            "activities": record["description"],
                            "website": record["url"],
                        },
                    )
                    if created:
                        records["created"] += 1
                        for field, value in TAG_LOOKUP.items():
                            if record.get(field):
                                funder.tags.add(funder_tags[value])
                    else:
                        records["updated"] += 1

    click.secho(
        "Created: {created}, Existing: {updated}".format(**records),
        fg="green",
    )
