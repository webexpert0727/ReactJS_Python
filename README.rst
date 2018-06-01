HookCoffee.com.sg
=================


Our stack
---------

Back-end:
    - Python 2.7
    - Django 1.10
    - PostgreSQL 9.6
    - Redis 3
    - Celery 4
    - PyTest
    - Gunicorn
    - Sentry
    - InfluxDB
    - Telegraf
    - Grafana
    - Docker (only for some services: Sentry, Telegraf, InfluxDB and Grafana)
    - Debian 9

Fron-end:
    - Jquery
    - Bootstrap 3
    - ReactJS
    - Redux + Sagas (a little bit ;)
    - Webpack & Babel

Third-party services:
    - Stripe
    - Mandrill & Mailchimp
    - Intercom
    - Typeform
    - DigitalOcean


Installation
------------

To simplify your introduction to the project, we recommend using Docker for local development.
Follow the instructions:

1. Install and run Docker in your local environment [`Mac <https://docs.docker.com/docker-for-mac/install/>`_, `Win <https://docs.docker.com/docker-for-windows/install/>`_, etc].

2. Create a new folder for the project::

    $ mkdir -p ~/hookcoffee_sg/{app_data/{logs,generated/{addresses,labels},assets/{media,static}},backups,hookcoffee} && cd ~/hookcoffee_sg/hookcoffee

3. Download and extract media files::

    $ curl https://hookcoffee.com.sg/media/new_dev/media.tar.gz | tar -xz -C ../app_data/assets

4. Clone the project repository::

    $ git clone --separate-git-dir ../.git git@github.com:ernesttyh/hookcoffee.git .

5. Create your own .env file based on .env.example::

    $ cp .env.example .env

6. Build the project::

    $ docker-compose -f docker-compose.yml -f docker-compose.dev.yml build app

**That's it! Now you can start up the project!**

.. code-block:: bash

    $ docker-compose -f docker-compose.yml -f docker-compose.dev.yml up app

Now open `http://0.0.0.0:8000/accounts/profile/ <http://0.0.0.0:8000/accounts/profile/>`_ and log in using credentials below:

:Login: dev@hookcoffee.com.sg
:Password: GKLJXhba8Wy3

**Congratulations!** You're up and running now. If anything gone wrong -- don't hesitate and tell us about it.


Usage
-----

Start
~~~~~

Using the environment variable ``$SYSTEM_UP_COMMAND`` specified in the ``.env`` file, you can specify the preferred way to start the system. By default, the system is started by using the django runserver on the 8000 port (*python manage.py runserver 0.0.0.0:8000*)

However, you can change the ``$SYSTEM_UP_COMMAND`` variable to ``gunicorn giveback_project.wsgi:application`` (or just unset the variable) and use Gunicorn + Nginx, in this case the website will be availible on the 80 port.
But since the real need for nginx in developing process around zero, the nginx as service was separated from the dependencies and can be started by a command::

    $ docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d nginx


Build front-end part
~~~~~~~~~~~~~~~~~~~~

Currently we have 2 "apps" that based on ReactJS, ES5+ and some another cool front-end stuff.

- **Shopping Cart**
- **Manager application** (used to process orders and other internal things)

To build these apps::

    $ yarn run build

    # or if you need to build only one of the applications:

    # app - currently now it's related only to Shopping Cart
    $ yarn run build:app
    $ yarn run build:manager

**Attention!**

::

    After pushing updates for these apps you must run build apps and collect static files. Don't forget it! It's a really important!

Also on your local environment you can run ``webpack-dev-server`` with Hot Module Replacement::

    $ yarn run start:app
    # or
    $ yarn run start:manager

Need more functionality? Check ``package.json``.


Dependencies
~~~~~~~~~~~~

If you or another developer has changed basic system dependencies, `package.json` or `requirements/*` files, just rebuild *the app image*::

    $ docker-compose -f docker-compose.yml -f docker-compose.dev.yml build --no-cache app


Multilanguage support
~~~~~~~~~~~~~~~~~~~~~

Currently we don't use it, but for case when it will be needed again::

    $ python manage.py makemessages -l zh
    $ python manage.py makemessages -l zh -d djangojs
    $ python manage.py compilemessages


Deploying
---------

1. Push the code on Github
2. Push the code on a test server.
3. If the testing was successful and you were given permission to deploy the code for production - do it, push the code on production server.

Ping developers_ to get credentials for a test server.


Documentation
-------------

Unfortunately, we don't have a documentation. So if you have any questions just ping the developers_.


FAQ
---

- How I can run Sentry?

    ::

        # Start up posgresql
        $ docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d sentry-postgres
        # Build the database
        $ docker-compose -f docker-compose.yml -f docker-compose.dev.yml run --rm sentry upgrade
        # Done. Run it!
        $ docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d sentry-postgres sentry-redis sentry-cron sentry-worker sentry

    For simplicity, you can also add the record ``0.0.0.0 sentry`` to your **hosts** file.
    Then go to http://sentry:9000/ and sign up.
    Go to http://sentry:9000/sentry/internal/settings/keys/ and copy the your DSN key
    (for example: *http://5c406...:7e6763...c@sentry:9000/1*).
    And save it in ``$SENTRY_DSN`` variable in your .env file.

- I pushed the code to the test/production server. What I should do next?

    You should connect to the server via ssh and in most cases it will be sufficient to run the command::

    $ do

    This will run the required environment, collect the static files and restart the application.

    Or if you need more control or for example you want to apply new migrations for the database, you can execute the commands that you need::

    $ # activate virtualenv
    $ cd /webapp
    $ . env/bin/activate
    $ cd giveback_project
    $
    $ # build front-end parts, if they have been changed
    $ yarn run build
    $
    $ # collect static files
    $ python manage.py collectstatic --noinput
    $
    $ # restart Celery
    $ sudo systemctl restart celery
    $ sudo systemctl restart celerybeat
    $
    $ # restart Nginx
    $ sudo systemctl restart nginx
    $
    $ # restart Redis
    $ sudo systemctl restart redis
    $
    $ # apply new migrations
    $ python manage.py migrate
    $
    $ # restart the app (via gunicorn)
    $ sudo systemctl restart webapp


Testing
-------

Most part of the project not covered by tests. However, the module responsible for order processing is completly covered by tests and you can check it::

    $ pytest --ds=giveback_project.settings.test

    # or from your host machine

    $ docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec app bash -c "gosu django bash -c 'source /var/www/env/bin/activate && pytest --ds=giveback_project.settings.test'"


Issues/Tasks
------------

In general, you will get tasks from three sources:

- Upwork messages
- Trello
- `Slack <https://hookcoffeeteam.slack.com/>`_ *(if need to check/fix something)*


Communication
-------------
- Upwork messages
- `Slack <https://hookcoffeeteam.slack.com/>`_


.. _developers:

Developers
----------

- Eugene aka `@elikho <https://github.com/elikho>`_ / elikho.hookcoffee@gmail.com


Links & Utils
-------------

- `sentry.hookcoffee.com.sg <http://sentry.hookcoffee.com.sg/>`_
- `metrics.hookcoffee.com.sg <http://metrics.hookcoffee.com.sg/>`_

- `test1.hookcoffee.com.sg <http://test1.hookcoffee.com.sg/>`_
- `sentry.test1.hookcoffee.com.sg <http://sentry.test1.hookcoffee.com.sg/>`_
- `metrics.test1.hookcoffee.com.sg <http://metrics.test1.hookcoffee.com.sg/>`_


TODO
-------------

- Completly rewrite the registration module. Not just refactoring!
  It's incredibly dirty and it's full of mistakes. Each line is a time bomb.
  Because this is one of the most important components of the system - it must be covered by tests (at least the back-end part). It is supposed to be written on ReactJS & Redux.
- Migrate from hstore to json[b] fields.
