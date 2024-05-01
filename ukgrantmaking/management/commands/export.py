import djclick as click

from ukgrantmaking.models import Funder, FunderNote, FunderTag, FunderYear, Grant
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
