RTM
=========
This is the RTM dashboard built on data collected by RapidPro.

Getting Started
================

Install dependencies
```
% python3 -m venv env
% source env/bin/activate
% pip install -r requirements.txt
```

You'll need to create the postgres db first
and you must create a file called **.env** at the root of the project with the following data where:

**<db_name>**, **<db_username>**, **<db_password>** consecutively are the data of the postgres db that was created;
**TOKEN_WORKSPACE_GLOBAL** is the token of the global workspace in rapidpro;
**SECRET_KEY** is a secret key for your project.

```
POSTGRES_DB=<db_name>
POSTGRES_USER=<db_username>
POSTGRES_PASSWORD=<db_password>
DEFAULT_DATABASE=postgresql://<db_username>:<db_password>@localhost/<db_name>
TOKEN_WORKSPACE_GLOBAL=
SECRET_KEY=

DEBUG=true
COMPRESS_ENABLED=false
COMPRESS_OFFLINE=false
REDIS_DATABASE=1
IS_DEV=true
```

Add all our models and create our superuser
```
% python manage.py migrate
% python manage createsuper
% python manage collectstatic
```

At this point everything should be good to go, you can start with:

```
% python manage.py runserver
```
