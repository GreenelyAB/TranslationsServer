# -*- coding: utf-8 -*-
# pylint: disable=protected-access
from threading import local
from functools import wraps
from dbquery.postgres import PostgresDB
from psycopg2.pool import ThreadedConnectionPool

import config


_CONNECTION_POOL = None


def _ensure_local(var_name, default):
    """ Ensure that var_name exists in _local on self, if not initialize it
    with default.
    """
    def _decorator(f):
        @wraps(f)
        def _new_f(self, *args, **kwds):
            if not hasattr(self._local, var_name):
                setattr(self._local, var_name, default)
            return f(self, *args, **kwds)
        return _new_f
    return _decorator


class _PostgresConnectionPoolDB(PostgresDB):

    def __init__(self, *args, **kwds):
        self._local = local()
        self._local._connection = None  # never use directly, use property!
        self._local._transaction_level = 0  # never use directly, use property!
        self._local._orig_retry = None  # never use directly, use property!
        super().__init__(*args, **kwds)

    @property
    @_ensure_local("_transaction_level", 0)
    def _transaction_level(self):
        return self._local._transaction_level

    @_transaction_level.setter
    @_ensure_local("_transaction_level", 0)
    def _transaction_level(self, value):
        self._local._transaction_level = value

    @property
    @_ensure_local("_connection", None)
    def _connection(self):
        return self._local._connection

    @_connection.setter
    @_ensure_local("_connection", None)
    def _connection(self, value):
        self._local._connection = value

    @property
    @_ensure_local("_orig_retry", None)
    def _orig_retry(self):
        return self._local._orig_retry

    @_orig_retry.setter
    @_ensure_local("_orig_retry", None)
    def _orig_retry(self, value):
        self._local._orig_retry = value

    def _connect(self):
        global _CONNECTION_POOL
        if _CONNECTION_POOL is None:
            _CONNECTION_POOL = ThreadedConnectionPool(
                config.DB_MIN_CONNECTIONS, config.DB_MAX_CONNECTIONS,
                **config.DB_PARAMS)
        if self._connection is not None:
            raise RuntimeError("Connection still exists.")
        self._connection = _CONNECTION_POOL.getconn()
        self._connection.set_session(autocommit=True)

    def close(self):
        if self._connection is not None:
            _CONNECTION_POOL.putconn(self._local._connection)
            self._connection = None
        super().close()


db = _PostgresConnectionPoolDB()
