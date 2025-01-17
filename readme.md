# UK Grantmaking Data

## Initial setup

```sh
python -m venv env
env\Scripts\activate
pip install wheel pip-tools
pip-compile
pip-sync
```

### With UV

```sh
uv venv
uv pip compile requirements.in -o requirements.txt
uv pip sync requirements.txt
```

#### Update dependencies

```sh
uv pip compile requirements.in -o requirements.txt
uv pip sync requirements.txt
```

### Setup Django

```sh
python manage.py migrate
python manage.py createsuperuser
```

### Run django server

```sh
python manage.py runserver
```

### Linting and code formatting

```sh
ruff check . --fix
ruff format .
```

## Setup on Dokku

### Initial app setup (on server)

```sh
# create app
dokku apps:create uk-grantmaking-data

# postgres
sudo dokku plugin:install https://github.com/dokku/dokku-postgres.git postgres
dokku postgres:create uk-grantmaking-data-db
dokku postgres:link uk-grantmaking-data-db uk-grantmaking-data

# letsencrypt
sudo dokku plugin:install https://github.com/dokku/dokku-letsencrypt.git
dokku letsencrypt:set uk-grantmaking-data emaillabs@threesixtygiving.org
dokku letsencrypt:enable uk-grantmaking-data
dokku letsencrypt:cron-job --add

# set secret key
# To generate use:
# `python -c "import secrets; print(secrets.token_urlsafe())"`
dokku config:set --no-restart uk-grantmaking-data SECRET_KEY='<insert secret key>'

# setup account directory
dokku storage:ensure-directory uk-grantmaking-data
dokku storage:mount uk-grantmaking-data /var/lib/dokku/data/storage/uk-grantmaking-data:/app/storage
dokku config:set uk-grantmaking-data --no-restart MEDIA_ROOT=/app/storage/media/

# setup hosts
dokku config:set uk-grantmaking-data --no-restart DEBUG=false ALLOWED_HOSTS="hostname.example.com"

# create superuser account
dokku run uk-grantmaking-data python manage.py createsuperuser
```

### Deploy the app for the first time (on local computer)

```sh
git remote add dokku dokku@SERVER_HOST:uk-grantmaking-data
git push dokku main
```

### After deployment (on server)

```sh
# create superuser account
dokku run uk-grantmaking-data python manage.py createsuperuser
```

## Commands for loading data

### Fetch commands

These commands fetch new or updated data from an external source.

#### `python manage.py fetch ftc`

Fetch updated data for all current funders from Find that Charity.

Command line options:

- `--debug`: Enable debug mode
- `--skip-funders`: Skip loading new funder information
- `--skip-financial`: Skip loading new financial information for funders

What the command does:

1. Funder data updates:
   1. Get a list of org ids of the current funders
   2. Fetch updated name, date registered, date removed and whether currently active from Find that Charity
   3. Update the `ukgrantmaking_funder` table with the updated data.
2. Funder financial information:
   1. Run the SQL queries from `python manage.py update financial-year` to ensure all funders have the needed financial years
   2. Get a list of all current funder financial years from the database
   3. Get a list of successor lookups from the database - this is where a funder has a "successor" organisation marked (i.e. they have re-registered with a different charity number or have merged with another organisation).
   4. Fetch updated financial records from Find that Charity.
   5. Match to the corrent funder_financial_year (including the `new_funder_financial_year_id` for organisations with a successor)
   6. Update the `ukgrantmaking_funderyear` table with the new records.

#### `python manage.py fetch grants`

Fetches updated grants data from the 360Giving Datastore.

Command line options:

- `db_con` - Connection to the 360Giving Database. Usually doesn't need to be specified as it is taken from the `TSG_DATASTORE_URL` environmental variable.

What the command does:

1. Work out the current financial year
2. Fetch all grants from the Datastore between the start and end dates specified in the current financial year
3. Calculate the `planned_dates_duration` field - either using the existing value, or calculating from `planned_dates_endDate` and `planned_dates_startDate`.
4. Fetch all grants from the [DCMS lottery database](https://nationallottery.dcms.gov.uk/) between the start and end dates.
5. Rename columns from the DCMS data to match the 360Giving data.
6. Mark grants where the recipient is "Grant to Individual" or "Grant Awarded to Individual", or where the description is "Athlete Performance Award" as grants to individuals.
7. Exclude grants from the DCMS data where it is already in the data from the 360Giving Datastore:
   1. Exclude any grants where the grant ID matches (including renaming the NLCF grant IDs from "DCMS-tnlcomfund-" to "360G-tnlcomfund-")
   2. Match grants based on:
      - Grant title
      - Amount awarded
      - Award date
      - Recipient organisation name
      - Funding organisation ID
8. Merge the two datasets into one
9. Remove any duplicate grant IDs
10. Ensure column formats are correct (amount awarded is a number, award date is a date, etc)
11. Add a financial year column
12. Save currencies to the database ([these need to be periodically checked to ensure they have exchanged rates](https://uk-grantmaking-data.360dokku1.vs.mythic-beasts.com/admin/ukgrantmaking/currencyconverter/))
13. Save grant records to the database
14. Update grant inclusions for government grants:
    - All grants not in central or devolved government are included by default
    - All grants with a recipient organisation ID starting with `GB-CHC-`, `GB-SC-` or `GB-NIC-` are included by default

#### `python manage.py fetch grant-recipients`

Fetch data for grant recipients from Find that Charity

What this command does:

1. Get a list of all grant recipients (excluding grants to individuals)
2. Check for any recipients that don't already have a `GrantRecipient` record, and create a record. Match this record to the grant object.
3. Update all existing `GrantRecipient` records with the type of recipient and their name from the latest grant to them.
4. Fetch updated data on all these recipient from Find that Charity. Update these records in the database
5. Fetch updated financial data for all these recipients from Find that Charity. Add a financial year and update these records in the database.

### Update commands

These commands perform procedures to update the data currently in the database,
without fetching any new data.

#### `python manage.py update financial-year`

This runs a series of SQL commands to keep the financial data up to date. The commands are:

1. Ensure every funder has a funder financial year for the current financial year
2. Set the current year to the correct year
3. Set the latest year to the correct year
4. Recalculate aggregate values for funder financial years
5. Update current funder financial years with the latest funder data
6. Ensure that the current funder financial year has the correct tags
7. Remove existing tags from the current funder financial year

#### `python manage.py update grants`

#### `python manage.py update grant-recipient-type`

### Deprecated commands

These commands were used for the initial construction of the database
for the 2024 UK Grantmaking publication but are no longer used.

#### `python manage.py fetch master-list`

Create a list of funders from an Excel sheet

#### `python manage.py fetch cleaned-data`

Create Funder years from a list of excel files

#### `python manage.py fetch tags`

Add tags to Funders from an Excel spreadsheet.
Should instead use the endpoint at `/grantmakers/upload`.

#### `python manage.py fetch fgt`

Used to import data from the back catalogue of Foundation Giving Trends.

## Export data as backup

```sh
dokku postgres:export uk-grantmaking-data-db > ~/uk-grantmaking-data-db-20251701.export
```
