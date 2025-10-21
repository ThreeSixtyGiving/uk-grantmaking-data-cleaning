1. **Change financial year** - in admin site, Financial Years: update new year to mark as 'Current' set to'Open' and prior year to 'Closed'.  Save changes.
2. **Fetch data from FTC** Access the server: `ssh root@uk-grantmaking-data.360dokku1.vs.mythic-beasts.com` Run `dokku run uk-grantmaking-data python manage.py fetch ftc`
3. **Update financial year** Run `dokku run uk-grantmaking-data python manage.py update financial-year`
4. **Fetch grants data from the datastore & Lottery DCMS database** Run `dokku run uk-grantmaking-data python manage.py fetch grants`
5. **Fetch Grant recipient data** Run `dokku run uk-grantmaking-data python manage.py fetch grant-recipient`
6. **Update currency conversion rates** In admin site, Currency Converters: Filter by rate 'Empty', vist XE via link and updatebased on units per ... 