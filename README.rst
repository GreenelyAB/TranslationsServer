TranslationsServer
==================

.. image:: https://api.travis-ci.org/GreenelyAB/TranslationsServer.svg?branch=master
    :target: https://travis-ci.org/GreenelyAB/TranslationsServer?branch=master

Manage, store and deliver translations.


Definition
----------

A *translation* starts out with a key, usually the English version of the text.
For each key there can be a translation for another language. That is the
second parameter for a translation.

A translation can also be country depended, the third parameter.

The last parameter specifies the plural version of the translation. This is
needed for when the translation refers to some amount and needs to be different
depending on what that amount is.


Rules for finding a translation
-------------------------------

The parameters for getting a translation are:

- **key**: the text to translate
- **lang**: the language for the translation, following
  `ISO 639-1 <https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes>`_
- **country** [optional] the country for the translation, following
  `ISO 3166-1 alpha-2 <https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2>`_
- **plural** [optional] the related value that defines the plural form of
  the translation

The steps taken to find a translation are:

- find all translations for the given key
- only keep the ones with the specified language
- from that list keep the ones with a matching country, if there are no entries
  with a matching country keep the ones without a specified country
- if a plural parameter was specified try to find entries with that plural
  value otherwise select the translation where no plural value was specified
- if more than one translations are left take the first one, if no translation
  is left take the key as the translation instead


Installation
============

- Prepare a `Postgres <https://www.postgresql.org/>`_ database and user.
- Install `npm <https://www.npmjs.com/>`_.
- Create and activate a
  `Python 3 virtual environment <https://docs.python.org/3/library/venv.html>`_.
- Clone/download the
  `project <https://github.com/GreenelyAB/TranslationsServer/releases>`_.
- Then go to that project folder and run:
  ::

      $ npm install
      $ export TRANSLATIONS_SERVER_DB_URL="<YOUR DATABASE URL>"
      $ grunt migrate
      $ cd src
      $ cp config_local.py.example config_local.py
- Review and edit this new file `config_local.py`.


Database URL example
--------------------

Connecting to a database named `test`on a local postgres server with user
`postgres` and no password: "`postgres://postgres:@127.0.0.1/test`"


Run
===

After completing the installation and activating the Python environment go to
the project folder and start a development server like this:
::

    $ cd src
    $ ./main.py


How you run your server in production depends on your production environment.

Run `./main.py --help` for port options.


Run tests
---------

Prepare an empty test database and configure it in through
`TRANSLATIONS_SERVER_TEST_DB_URL` in `config_local.py`. Then go to the project
folder and run:
::

    $ cd test
    $ ./run_tests.py


Add and edit translations
=========================

Theres are each a table for languages and countries. If a new alnguage or
country is needed those tables need to be updated first:
::

    translations_server=# INSERT INTO languages (language_code, name)
    VALUES ('en', 'English');
    translations_server=# INSERT INTO countries (country_code, name)
    VALUES ('US', 'United States of America');


There is no support for states, yet. Optionally one could modify the countrie
codes to include the states information.

All translations then reside in the `translations` table, which contains:

- **translation_id**
- **translation_key**: The key (original text) for the translation.
- **language_id**: References `languages`.
- **country_id**: References `countries`.
- **plural**: The plural count (variation) for which this translation is for.
- **translation_text**: The translated text.

The table can be manipulated by either working on it directly or by using a
admin interface such as
`Django admin <https://docs.djangoproject.com/en/dev/ref/contrib/admin/>`_ (use
`Multiple databases
<https://docs.djangoproject.com/en/dev/topics/db/multi-db/>`_).


ZMQ protocol
============

The server takes on request at the configured port number and responds with a
replay to each request.

Each request shall send at least 4 frames containing:

- language
- country or ```""```
- key
- plural or ```""```

Each request may further contain more frames in pairs, each containing:

- key
- plural or ```""```

For example:
::

    "sv"
    ""
    "User not active"
    ""

An example requesting two translations:
::

    "sv"
    ""
    "User not active"
    ""
    "User not found"
    ""

The server shall then respond with either exactly one frame containing an
empty string or as many frames as keys where send, each containing the
translation for the corresponding key.

The response with only one frame containing an empty strings signals a server
error.

Response example for requesting two keys:
::

     "Användare ej aktiv"
     "User not found"
