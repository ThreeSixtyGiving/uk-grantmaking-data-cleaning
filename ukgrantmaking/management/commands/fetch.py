import djclick as click

from ukgrantmaking.management.commands.funders.fetch_cleaned_data import cleaned_data
from ukgrantmaking.management.commands.funders.fetch_fgt import fgt
from ukgrantmaking.management.commands.funders.fetch_ftc import ftc
from ukgrantmaking.management.commands.funders.fetch_master_file import master_list
from ukgrantmaking.management.commands.funders.fetch_tags import tags
from ukgrantmaking.management.commands.grants.fetch_grant_recipients import (
    grant_recipients,
)
from ukgrantmaking.management.commands.grants.fetch_grants import grants


@click.group(invoke_without_command=False)
def main():
    pass


main.add_command(master_list, "master-list")
main.add_command(ftc, "ftc")
main.add_command(cleaned_data, "cleaned-data")
main.add_command(tags, "tags")
main.add_command(fgt, "fgt")


main.add_command(grants, "grants")
main.add_command(grant_recipients, "grant-recipients")
