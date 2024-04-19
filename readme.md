# UK Grantmaking Data

## Initial setup

```
python -m venv env
env\Scripts\activate
pip install wheel pip-tools
pip-compile
pip-sync
```

### Setup Django

```
python manage.py migrate
python manage.py createsuperuser
```

### Run django server

```
python manage.py runserver
```

### Linting and code formatting

```
ruff check . --fix
ruff format .
```

## Setup on Dokku

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

```
git remote add dokku dokku@SERVER_HOST:uk-grantmaking-data
git push dokku main
```
