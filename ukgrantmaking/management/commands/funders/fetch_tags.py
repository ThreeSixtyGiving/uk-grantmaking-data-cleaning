import djclick as click
import numpy as np
import pandas as pd

from ukgrantmaking.models import Funder, FunderTag


@click.command()
@click.argument("file")
@click.option("--orgid-column", default="org_id")
@click.option("--tag-column", default="tag")
@click.option("--tag", default=None)
@click.option("--name-column", default="name")
def tags(file, orgid_column, tag_column, tag, name_column):
    click.secho("Opening {}".format(file), fg="green")
    df = pd.read_excel(file)

    if not tag and tag_column not in df.columns:
        raise click.ClickException("Tag column not found in file and no tag provided")

    funder_tags = {}
    if tag_column in df.columns:
        for tag_record in df[tag_column].unique():
            tag_record = tag_record.strip()
            funder_tag, tag_created = FunderTag.objects.get_or_create(
                tag=tag_record,
            )
            funder_tags[tag_record] = funder_tag
    if tag:
        tag = tag.strip()
        funder_tags[tag], tag_created = FunderTag.objects.get_or_create(
            tag=tag,
        )

    records = {
        "Funder created": 0,
        "Funder found": 0,
    }
    for index, record in df.replace({np.nan: None}).iterrows():
        # skip if no orgid
        if not getattr(record, orgid_column, None):
            continue

        defaults = {}
        if hasattr(record, name_column):
            defaults["name_registered"] = getattr(record, name_column)
        funder, created = Funder.objects.get_or_create(
            org_id=getattr(record, orgid_column),
            defaults=defaults,
        )
        if tag:
            funder.tags.add(funder_tags[tag])
        if isinstance(getattr(record, tag_column, None), str):
            tag_value = getattr(record, tag_column).strip()
            funder.tags.add(funder_tags[tag_value])
        records["Funder created" if created else "Funder found"] += 1

    for key, value in records.items():
        click.secho("{}: {}".format(key, value), fg="green")
