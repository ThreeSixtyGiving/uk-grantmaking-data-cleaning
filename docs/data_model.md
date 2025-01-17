## Concepts

### "Registered" vs "Manual" data

To preserve data integrity, the data models make use of the concept of "registered" vs "manual" data. "Registered" data
comes from an external source, like the Charity Commission or 360Giving published data. This data is expected to be
overwritten at any time - for example if new data is fetched from the Charity Commission.

Because this data can be overwritten at any time, any changes that we want to make are stored in a separate field (the "manual" field). When a value is present in this field, it is used instead of the "registered" value.

For example, when looking at the funder name:

| `name_registered`                | `name_manual`              | `name`                             |
| -------------------------------- | -------------------------- | ---------------------------------- |
| **Name from an official source** | **Name entered by a user** | **The name shown in data outputs** |
| "Test Charity"                   | [empty]                    | "Test Charity"                     |
| "Test Charity"                   | "Edited Charity"           | "Edited Charity"                   |

## General models

### FinancialYear

The `FinancialYear` model represents a year used in UK Grantmaking, e.g. "2022-23". Financial records are attached to this financial year.

#### FinancialYear attributes

| Attribute            | Description                                                                                                                                        |
| -------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| `fy`                 | The name for the financial year, e.g "2022-23"                                                                                                     |
| `current`            | Whether the financial year is the current year. Only one FinancialYear can have this value                                                         |
| `status`             | Whether the financial year is "Open" (data cleaning is ongoing), "Closed" (data cleaning has finished) or "Future" (data cleaning not yet started) |
| `funders_start_date` | The first date at which a financial year end from a funder year will be included. Usually 1st May in the first year, e.g. 2022-05-01               |
| `funders_end_date`   | The last date at which a financial year end from a funder year will be included. Usually 30th April in the last year, e.g. 2023-04-30              |
| `grants_start_date`  | The first date at which an award date from a Grant will be included. Usually 1st April in the first year, e.g. 2022-04-01                          |
| `grants_end_date`    | The last date at which an award date from a Grant will be included. Usually 31st March in the last year, e.g. 2023-03-31                           |
| `first_year`         | The first year of the financial year, e.g. 2022 - a calculated field                                                                               |
| `last_year`          | The last year of the financial year, e.g. 2023 - a calculated field                                                                                |

## Grantmakers models

### Funder

The `Funder` model represents an organisation record. This record might be based on external data (sourced from Find that Charity), or it may have an organisation ID that we have made up.

#### Funder attributes

| Attribute                     | Description                                                                                                                                                                        |
| ----------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `name`                        | Funder name - can be overridden if supplied from registered data                                                                                                                   |
| `included`                    | True / False - whether the funder should be included in UK Grantmaking                                                                                                             |
| `makes_grants_to_individuals` | True / False - Whether this funder makes grants to individuals                                                                                                                     |
| `segment`                     | This funder's segment                                                                                                                                                              |
| `tags`                        | A list of tags assigned to this charity. Including which external lists it appeared on.                                                                                            |
| `successor`                   | If the funder has been replaced by another record, this holds the new record.                                                                                                      |
| `status`                      | Whether the funder is "Checked", "Unchecked" or "New". This field isn't the main record of whether a funder is checked - instead this is held in the `FunderFinancialYear` record. |
| `date_of_registration`        | Date of registration from official register. Cannot be overridden.                                                                                                                 |
| `date_of_removal`             | Date of removal from official register. Cannot be overridden.                                                                                                                      |
| `active`                      | Whether the funder is currently active. Cannot be overridden.                                                                                                                      |
| `activities`                  | A description of the funder from an official register.                                                                                                                             |
| `website`                     | The funder's website from an official register.                                                                                                                                    |
| `notes`                       | Any notes added about this funder by users.                                                                                                                                        |

### Funder Financial Year

Each funder has a number of Funder Financial Year records, that represent a snapshot of the funder at a particular time. A funder financial year record is available for every funder for each financial year (e.g. 2022-23).

The `FunderFinancialYear` record only stores a copy of the `included`, `makes_grants_to_individuals`, `segment` and `tags` attributes for that funder. While a financial year is "Open" and "Current", any changes made to
the `Funder` model in these attributes will be copied to the equivalent `FunderFinancialYear`. However, when a financial year is marked as "Closed" or not "Current" then the `FunderFinancialYear` record is not updated.

#### FunderFinancialYear attributes

| Attribute                     | Description                                                                             |
| ----------------------------- | --------------------------------------------------------------------------------------- |
| `funder`                      | The funder this record belongs to                                                       |
| `financial_year`              | The financial year this record belongs to                                               |
| `included`                    | True / False - whether the funder should be included in UK Grantmaking                  |
| `makes_grants_to_individuals` | True / False - Whether this funder makes grants to individuals                          |
| `segment`                     | This funder's segment                                                                   |
| `tags`                        | A list of tags assigned to this charity. Including which external lists it appeared on. |
| `checked`                     | Whether this record has been checked by a user                                          |
| `checked_on`                  | The time at which this record was marked as checked                                     |
| `checked_by`                  | The user who marked this record as checked                                              |

#### FunderFinancialYear financial data

The `FunderFinancialYear` doesn't store any of its own financial data (e.g. the value of grants to individuals). These figures are instead kept in `FunderYear` records attached to a `FunderFinancialYear`. In
most cases the `FunderFinancialYear` record will have only one `FunderYear`, however there are reasons why there might be more than one:

- The funder changed financial year end, resulting in a financial year with less than 12 months. If this falls at the right time, this can result in two `FunderYear` records being attached to the same `FunderFinancialYear`, but with each one having different financial year ends.
- The funder has had a `successor` funder set. In this case, the successor funder will have the financial records from the predecessor attached to them instead. This can result in two `FunderYear` records with different financial year ends.

The `FunderFinancialYear` record does stores a read-only copy of financial records from the `FunderFinancialYear`. These records cannot be edited, and are replaced every time the `FunderYear` is saved.

When a `FunderFinancialYear` has more than 2 `FunderYears`, the financial records are worked out either by summing the `FunderYear` values (for income and expenditure items) or by taking the latest value (for balance sheet or employment items). The values included are:

| Attribute                                          | Produced by | Note                                            |
| -------------------------------------------------- | ----------- | ----------------------------------------------- |
| `income`                                           | SUM         |                                                 |
| `income_investment`                                | SUM         |                                                 |
| `spending`                                         | SUM         |                                                 |
| `spending_investment`                              | SUM         |                                                 |
| `spending_charitable`                              | SUM         |                                                 |
| `spending_grant_making`                            | SUM         |                                                 |
| `spending_grant_making_individuals`                | SUM         |                                                 |
| `spending_grant_making_institutions_charitable`    | SUM         | Not currently included                          |
| `spending_grant_making_institutions_noncharitable` | SUM         | Not currently included                          |
| `spending_grant_making_institutions_unknown`       | SUM         | (Shown as `spending_grant_making_institutions`) |
| `spending_grant_making_institutions`               | SUM         | Not currently included                          |
| `total_net_assets`                                 | LATEST      |                                                 |
| `funds`                                            | LATEST      |                                                 |
| `funds_endowment`                                  | LATEST      |                                                 |
| `funds_restricted`                                 | LATEST      |                                                 |
| `funds_unrestricted`                               | LATEST      |                                                 |
| `employees`                                        | LATEST      |                                                 |

### Funder Year

The `FunderYear` model holds data about a financial record for a given funder, given a financial year end. Generally there is one `FunderYear` per `FunderFinancialYear` but this is not always the case.

The `FunderYear` attributes make use of `_registered` and `_manual` variants, with the `_manual` value used if present, otherwise the `_registered` value is used. The grantmaking attributes also have a `_360giving` variant which is used when the

| Attribute                                          | `_registered` source                  | `_360giving` source            | Note                                                                                         |
| -------------------------------------------------- | ------------------------------------- | ------------------------------ | -------------------------------------------------------------------------------------------- |
| `financial_year_end`                               | CCEW[^CCEW], CCNI[^CCNI], OSCR[^OSCR] |                                |                                                                                              |
| `financial_year_start`                             | CCEW, CCNI, OSCR                      |                                |                                                                                              |
| `income`                                           | CCEW, CCNI, OSCR                      |                                |                                                                                              |
| `income`                                           | CCEW, CCNI, OSCR                      |                                |                                                                                              |
| `income_investment`                                | CCEW, CCNI, OSCR                      |                                | Thresholds apply (eg >£500k income for CCEW)                                                 |
| `spending`                                         | CCEW, CCNI, OSCR                      |                                |                                                                                              |
| `spending_investment`                              | CCEW                                  |                                | Thresholds apply (eg >£500k income for CCEW)                                                 |
| `spending_charitable`                              | CCEW, CCNI, OSCR                      |                                | Thresholds apply (eg >£500k income for CCEW)                                                 |
| `spending_grant_making`                            |                                       |                                | Calculated only.                                                                             |
| `spending_grant_making_individuals`                |                                       | 360Giving[^360Giving], NL[^NL] |                                                                                              |
| `spending_grant_making_institutions_charitable`    |                                       |                                | Not currently included                                                                       |
| `spending_grant_making_institutions_noncharitable` |                                       |                                | Not currently included                                                                       |
| `spending_grant_making_institutions_unknown`       | CCEW                                  | 360Giving, NL                  | Thresholds apply (eg >£500k income for CCEW) (Shown as `spending_grant_making_institutions`) |
| `spending_grant_making_institutions`               |                                       |                                | Calculated only. Not currently included                                                      |
| `total_net_assets`                                 | CCEW                                  |                                | Thresholds apply (eg >£500k income for CCEW)                                                 |
| `funds`                                            | CCEW                                  |                                | Thresholds apply (eg >£500k income for CCEW)                                                 |
| `funds_endowment`                                  | CCEW                                  |                                | Thresholds apply (eg >£500k income for CCEW)                                                 |
| `funds_restricted`                                 | CCEW                                  |                                | Thresholds apply (eg >£500k income for CCEW)                                                 |
| `funds_unrestricted`                               | CCEW                                  |                                | Thresholds apply (eg >£500k income for CCEW)                                                 |
| `employees`                                        | CCEW, CCNI                            |                                | Thresholds apply (eg >£500k income for CCEW)                                                 |

[^CCEW]: Charity Commission for England and Wales (from Find that Charity)
[^OSCR]: Scottish Charity Regulator (from Find that Charity)
[^CCNI]: Charity Commission for Northern Ireland (from Find that Charity)
[^360Giving]: 360Giving Publishers (from 360Giving Datastore)
[^NL]: National Lottery Grants data (from DCMS data tool)
