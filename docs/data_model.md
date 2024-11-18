## Concepts

### "Registered" vs "Manual" data

To preserve data integrity, the data models make use of the concept of "registered" vs "manual" data. "Registered" data
comes from an external source, like the Charity Commission or 360Giving published data. This data is expected to be
overwritten at any time - for example if new data is fetched from the Charity Commission.

Because this data can be overwritten at any time, any changes that we want to make are stored in a separate field (the "manual" field). When a value is present in this field, it is used instead of the "registered" value.

For example, when looking at the funder name:

| `name_registered` | `name_manual`    | `name` - the name shown in data outputs |
| ----------------- | ---------------- | --------------------------------------- |
| "Test Charity"    | [empty]          | "Test Charity"                          |
| "Test Charity"    | "Edited Charity" | "Edited Charity"                        |

## Grantmakers models

### Funder

The funder model represents an organisation record. This record might be based on external data (sourced from Find that Charity), or it may have an organisation ID that we have made up.

#### Funder attributes

| Attribute                     | Description                                                                             |
| ----------------------------- | --------------------------------------------------------------------------------------- |
| `name`                        | Funder name - can be overridden if supplied from registered data                        |
| `included`                    | True / False - whether the funder should be included in UK Grantmaking                  |
| `makes_grants_to_individuals` | True / False - Whether this funder makes grants to individuals                          |
| `segment`                     | This funder's segment                                                                   |
| `tags`                        | A list of tags assigned to this charity. Including which external lists it appeared on. |
| `successor`                   | If the funder has been replaced by another record, this holds the new record.           |
