# How to fetch/update the data from FindThatCharity (FTC) 
1. Open a Windows terminal
2. Enter password
3. Run <code> ssh root@uk-grantmaking-data.360dokku1.vs.mythic-beasts.com </code> to access live database.
4. Run <code> dokku run uk-grantmaking-data python manage.py fetch ftc </code> to fetch latest grantmaker data from FTC
5. Run <code> dokku run uk-grantmaking-data python manage.py fetch grant-recipients </code> to fetch latest recipient organisation data from FTC
6. Run <code> dokku run uk-grantmaking-data python manage.py fetch grants </code> to fetch latest grants data

More information can be found in README [Commands for loading data](https://github.com/ThreeSixtyGiving/uk-grantmaking-data-cleaning?tab=readme-ov-file#commands-for-loading-data).