# -*- coding: utf-8 -*-
# pylint: disable=protected-access
from os import environ
from os.path import abspath
from random import choice
from subprocess import Popen
from urllib.parse import urlparse as _urlparse

import config
from translations_server.lib import postgres_db, db


_migrated_test_db = False

# TEST_DB is not actually in config because it is not needed ever for prod
# but if you set it in config_local it will be imported into config.
# If not and you run the tests this will tell you to set it.
try:
    _test_db_url = _urlparse(config.TRANSLATIONS_SERVER_TEST_DB_URL)

    TEST_DB_PARAMS = {
        "database": _test_db_url.path[1:],
        "user": _test_db_url.username,
        "password": _test_db_url.password,
        "host": _test_db_url.hostname
    }
except AttributeError:
    raise AttributeError("Please set TEST_DB in config_local")


def _migrate_test_db():
    global _migrated_test_db
    if not _migrated_test_db:
        env = dict(environ)
        env[config.DB_ENV] = config.TRANSLATIONS_SERVER_TEST_DB_URL
        with open('/dev/null', 'w') as devnull:
            p = Popen(
                ["grunt", "migrate:up"], cwd=abspath("../"), env=env,
                stdout=devnull)
            p.wait()
            if p.returncode != 0:
                raise RuntimeError(
                    "Clean DB task failed: {}".format(p.returncode))
        _migrated_test_db = True


def _reset_connection():
    db.close()
    if postgres_db._CONNECTION_POOL is not None:
        postgres_db._CONNECTION_POOL.closeall()
    postgres_db._CONNECTION_POOL = None


class PostgresTestDB():

    _orig_db_name = None

    @classmethod
    def setUpClass(cls):
        if cls._orig_db_name is not None:
            cls.tearDownClass()
        params = config.DB_PARAMS  # shortcut, pylint: disable=no-member
        template_db = TEST_DB_PARAMS["database"]
        _migrate_test_db()
        cls._orig_db_name = params["database"]
        new_db_name = (
            "test_" + "".join(choice("1234567890") for _ in range(5)))
        db.execute(
            "CREATE DATABASE {} WITH TEMPLATE {} OWNER {}".format(
                new_db_name, template_db, params["user"]), [])
        _reset_connection()  # connect to new DB with next query
        params["database"] = new_db_name

    @classmethod
    def tearDownClass(cls):
        if cls._orig_db_name is not None:
            params = config.DB_PARAMS  # shortcut, pylint: disable=no-member
            _reset_connection()  # close connection to the used test database
            db_name = params["database"]
            params["database"] = cls._orig_db_name
            cls._orig_db_name = None
            db.execute("DROP DATABASE IF EXISTS " + db_name, [])
