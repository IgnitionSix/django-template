#! /bin/sh
# && python manage.py loaddata 
cd baseapp && python manage.py migrate --settings=app.settings.local && python manage.py runserver 0.0.0.0:8000 --settings=app.settings.local