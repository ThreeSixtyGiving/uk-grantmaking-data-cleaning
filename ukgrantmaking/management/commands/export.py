import djclick as click

from ukgrantmaking.models.funder import Funder, FunderNote, FunderTag
from ukgrantmaking.models.funder_year import FunderYear
from ukgrantmaking.models.grant import Grant
from ukgrantmaking.views import export_all_data


@click.group(invoke_without_command=False)
def main():
    pass


@main.command()
@click.argument("filename", type=click.Path())
def grants(filename):
    models = [Grant]
    export_all_data(models, filename)


@main.command()
@click.argument("filename", type=click.Path())
def funders(filename):
    models = [Funder, FunderYear, FunderTag, FunderNote]
    export_all_data(models, filename)
