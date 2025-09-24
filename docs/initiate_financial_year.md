# Initiate a new financial year

## 1. Update which Financial Year is current

In django admin, visit the [Financial Year admin page](/admin/ukgrantmaking/financialyear/).
Make the following changes:

- Tick "Current" for the new financial year
- Untick "Current" for all other financial years (only one row should be ticked)
- Mark the new financial year as "Open", and all previous years as "Closed". Future years should be marked as "Future".

## 2. Run update financial year

```sh
python manage.py update financial-year
```

This ensures that there are Funder Financial Years for all the funders in the database
for the newly created data.

## 2. Run Fetch FTC

```sh
python manage.py fetch ftc
```
