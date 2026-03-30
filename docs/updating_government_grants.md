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


