import djclick as click

from ukgrantmaking.management.commands.funders.update_financial_year import (
    financial_year,
)
from ukgrantmaking.management.commands.grants.update_grants import grants
from ukgrantmaking.management.commands.grants.update_recipient_type import (
    recipient_type,
)


@click.group(invoke_without_command=False)
def main():
    pass


main.add_command(financial_year, "financial-year")
main.add_command(grants, "grants")
main.add_command(recipient_type, "grant-recipient-type")
