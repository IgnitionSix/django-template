# django-template

The Ignition 6 django-template project is a mildly opionated framework for creating modern web apps with [Django](https://www.djangoproject.com), [Django Rest Framework](https://www.django-rest-framework.org), [Tailwind](https://tailwindcss.com) , [django-tailwind](https://github.com/timonweb/django-tailwind), [Elasticsearch](https://www.elastic.co) and [HTMX](https://htmx.org). It has built-in github workflow actions to run your tests automatically as part of your build process.


## prerequisites
 - Docker, Docker Compose

To get going, fork the project, clone it locally, then `cd` into the directory that you created.

Create a virtual environment by running `python -m venv .venv && source .venv/bin/activate && pip install -r appimage/baseapp/requirements.txt`.

Run `docker-compose up -d` and the stack will bring itself up. Database Migrations run automatically on container startup.

To verify that everything is working, load [http://localhost:8000/](http://localhost:8000/) and you should see the default page. Click the htmx test button, and you should see `{'message': 'This is a return value from the API!'}` show up dynamically.

The default project layout has a folder for `api`, a django-rest-framework based API, and `home` the default webapp. `api` and `home` are responsible for managing their own urls via the `urls.py` in their root. Templates are shared across all apps, and live in the `appimage/baseapp/theme/templates` directory. Each app has its own subdirectory.

Assets are automatically minified and delivered via the `django-compressor` project.

If you add an app, remember to add it to the `baseapp/app/settings/base.py` `INSTALLED_APPS`

If you make changes to `requirements.txt`, you'll want to run `docker-compose down && docker-compose build && docker-compose up -d`