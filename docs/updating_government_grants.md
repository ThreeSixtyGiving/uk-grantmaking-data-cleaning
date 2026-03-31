# Updating government grants

Government grants data behaves differently to other grants data sources, although
it still comes from the 360Giving Datastore.

## Data loading

Because of inconsistencies with how the award dates are recorded in government grants
data, not all grants would be correctly loaded if it was included in the normal
data upload.

To get around this, we need to include the file identifier for the latest government data
file when running the fetch grants process. The file identifier can be found by running
this query against the Datastore Database (not the database for this site):

```sql
SELECT ds.id,
    ds."data"->>'title' AS "file_title",
    ds."data"->>'issued' AS "issued",
    ds."data"->>'identifier' AS "identifier"
FROM db_sourcefile ds
    INNER JOIN db_sourcefile_latest sl
        ON ds.id = sl.sourcefile_id
    INNER JOIN db_latest l
        ON sl.latest_id = l.id 
WHERE "data"->'publisher'->>'prefix' = '360G-cabinetoffice'
    AND l.series = 'CURRENT'
ORDER BY 3 DESC
```

The `identifier` found in column 4 is the one you need. The identifier for
2024-25 was `a00P400000l2vdSIAQ`.

To run the fetch grants process with this identifier, run:

```sh
python manage.py fetch grants --extra-file=a00P400000l2vdSIAQ
```

This will ensure that grants from that file are included, and also that
any grants in that file will have an award date manually set to 
the start date of the financial year if they are from before or the
end date if they are from after.

## Arms Length Bodies

Another change we make to the government grants data is to change the 
linked funder for grants which are assigned to a Government Department
but managed by an arms-length body. 

By default, these grants have a funder ID based on their managing department,
which is given in the `funding_organisation_id` and `funding_organisation_name`
fields. But the Arms-Length Body / NDPB that actually runs this funding is
found within the `funding_organisation_department` field.

Where there is an existing funder with the same name as something in the 
`funding_organisation_department` this will be set as the linked funder
when the `python manage.py update grants` process is run. Any grants
from government which have a funding organisation department that is not
found will be set as blank, so will need to be dealt with manually.

**Note**: Grants from Visit England and Visit Britain are combined under 
one department in the government data, so will also need to be dealt with manually.

### Dealing with missing ALBs

@TODO: write this section.

## Recipient type and exclusions

The `inclusion` field on the grants object determines whether a grant should be 
included in the final analysis.

Most grants are marked as "Included" by default, but government grants are instead
marked as "Unsure", meaning they need to be checked. Whether a government grant is 
included or excluded from the analysis is based on the type of recipient:

| Recipient type             | Included / Excluded               |
|----------------------------|-----------------------------------|
| Education                  | Excluded as Education grant       |
| Government department      | Excluded as government transfer   |
| Local Authority            | Excluded as Local Authority grant |
| NHS                        | Excluded as government transfer   |
| NDPB                       | Excluded as government transfer   |
| Overseas government        | Excluded as overseas government   |
| Private sector             | Excluded as Private sector grant  |
| University                 | Excluded as grant to University   |
| Charity                    | Included                          |
| Community Interest Company | Included                          |
| Mutual                     | Included                          |
| Non Profit Company         | Included                          |

Any grants left as "Unsure" are also included, so it is important to deal
with the bulk of the "Unsure" grants. The inclusion status of grants can also 
be set manually on the grant record

Recipient type and inclusion status are determined through a mixture of manual and automatic processes:

- In the `fetch grants` command:
    - all new government grants are set to "Unsure" when the records are imported.
    - Any Unsure grants where the recipient ID starts with "GB-CHC-", "GB-SC-" or "GB-NIC-"
      are set to included
- In the `fetch grant-recipients` command:
    - All grant recipients (excluding grants to individuals) are given a grant recipient record.
      This record will have a default `type` based on the recipient type given to the grant. This 
      is generally "Organisation" by default.
- In the `update grant-recipients` command:
    - A series of recipient types are applied based on the Org ID of the recipients
    - A process checks the company type for recipients with a company number and applies a recipient type to them
    - The `recipient_type_manual` from the grant recipient is applied to the grant if it is not already filled
    - Any unsure rows are classified based on the new recipient types.

To change the recipient type manually, you can use [the Grant Recipient admin page](/admin/ukgrantmaking/grantrecipient/?o=6) to find recipients. Ordering by the "Total grant amount unsure" field will show the recipients
with the largest amount of money in the "Unsure" category. The type manual can be changed from the grant recipient list page
or from an individual grant recipient page.

Changing the grant recipient type on these pages will then update the grant recipient type and inclusion status.