# -*- coding: utf-8 -*-
from logging import ERROR, getLogger
from unittest.case import TestCase
from unittest.mock import patch

from zmq import Context, Poller, POLLIN, LINGER, ROUTER, DEALER

from translations_server.db import _insert_translation, _insert_language, \
    _insert_country
from translations_server.server import _SYNC_ENDPOINT, _REQUEST_ENDPOINT, \
    _shut_down_workers, _start_workers
from translations_server_test.db_utils import PostgresTestDB


_ENCODING = "utf-8"

_LANGUAGE = "sv"  # something that is there by default

_LANGUAGE2 = "en"  # something that is there by default

_COUNTRY = "SE"  # something that is there by default

_KEY1 = "key1"

_TRANSLATION1 = "k1"

_KEY2 = "key2"

_TRANSLATION2_A = "k2_a"

_TRANSLATION2_B = "k2_b"

_KEY3 = "key3"

_TRANSLATION3_A = "k3_a"

_TRANSLATION3_B = "k3_b"

_KEY4 = "key4"

_TRANSLATION4_A = "k4_a"

_TRANSLATION4_B = "k4_b"

_TRANSLATION4_C = "k4_c"

_TRANSLATION4_D = "k4_d"

_KEY5 = "key5"

_TRANSLATION5_A = "k5_a"

_TRANSLATION5_B = "k5_b"

_TIMEOUT = 300  # msec


class TestServer(PostgresTestDB, TestCase):
    """ Run tests by creating a worker and making request to that worker to get
    translations.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        lang_id = _insert_language(_LANGUAGE, _LANGUAGE)
        lang2_id = _insert_language(_LANGUAGE2, _LANGUAGE2)
        country_id = _insert_country(_COUNTRY, _COUNTRY)
        # Add keys, 1 for each test in the required variations.
        _insert_translation(_KEY1, lang_id, None, None, _TRANSLATION1)
        _insert_translation(_KEY2, lang_id, None, None, _TRANSLATION2_A)
        _insert_translation(_KEY2, lang_id, country_id, None, _TRANSLATION2_B)
        _insert_translation(_KEY3, lang_id, None, None, _TRANSLATION3_A)
        _insert_translation(_KEY3, lang_id, None, 1, _TRANSLATION3_B)
        _insert_translation(_KEY4, lang_id, None, None, _TRANSLATION4_A)
        _insert_translation(_KEY4, lang_id, country_id, None, _TRANSLATION4_B)
        _insert_translation(_KEY4, lang_id, None, 1, _TRANSLATION4_C)
        _insert_translation(_KEY4, lang_id, country_id, 1, _TRANSLATION4_D)
        _insert_translation(_KEY5, lang_id, None, None, _TRANSLATION5_A)
        _insert_translation(_KEY5, lang2_id, None, None, _TRANSLATION5_B)

    @patch.object(getLogger("translations_server.server"), "level", ERROR)
    def _request_translation(self, language, country, key, plural):
        """ Start up a worker, sync it and then send it a translation request.

        Returns the result, shuts down the worker at the end as well.

        Fails the current test, if something goes wrong.
        """
        request = [
            language, country if country is not None else "", key,
            str(plural) if plural is not None else ""]
        request = [x.encode(_ENCODING) for x in request]
        context = Context()
        # Create synchronization and backend sockets.
        try:
            sync_socket = context.socket(ROUTER)
            try:
                sync_socket.bind(_SYNC_ENDPOINT)
                backend = context.socket(DEALER)
                try:
                    backend.bind(_REQUEST_ENDPOINT)
                    worker_threads, worker_identities = _start_workers(
                        context, sync_socket, 1, _TIMEOUT)
                    poller = Poller()
                    poller.register(backend, POLLIN)
                    poller.register(sync_socket, POLLIN)
                    # Send request.
                    backend.send_multipart(
                        [worker_identities[0], b""] + request)
                    sockets = dict(poller.poll(_TIMEOUT))
                    # Shutdown worker.
                    _shut_down_workers(
                        sync_socket, worker_threads, worker_identities,
                        _TIMEOUT / 1000.0)
                    if backend in sockets:
                        # Return translation.
                        return backend.recv_multipart()[2].decode("utf-8")
                    self.fail("Worker did not response the request in time.")
                finally:
                    backend.set(LINGER, 0)
                    backend.close()
            finally:
                sync_socket.set(LINGER, 0)
                sync_socket.close()
        finally:
            context.destroy(linger=0)

    def test_no_country_no_plural(self):
        """ Get a translation when no plural and no country variation exists.
        """
        translation = self._request_translation(_LANGUAGE, None, _KEY1, None)
        self.assertEqual(translation, _TRANSLATION1)

    def test_country_no_plural(self):
        """ Get a translation with a country variation. """
        translation = self._request_translation(
            _LANGUAGE, _COUNTRY, _KEY2, None)
        self.assertEqual(translation, _TRANSLATION2_B)  # and not 2_A

    def test_no_country_plural(self):
        """ Get a translation with a plural variation. """
        translation = self._request_translation(_LANGUAGE, None, _KEY3, 1)
        self.assertEqual(translation, _TRANSLATION3_B)  # and not 3_A

    def test_country_plural(self):
        """ Add all country and plural combination and try to get each
        corresponding translation.
        """
        translation = self._request_translation(_LANGUAGE, _COUNTRY, _KEY4, 1)
        self.assertEqual(translation, _TRANSLATION4_D)  # not A or B or C
        translation = self._request_translation(
            _LANGUAGE, _COUNTRY, _KEY4, None)
        self.assertEqual(translation, _TRANSLATION4_B)  # not A or C or D
        translation = self._request_translation(_LANGUAGE, None, _KEY4, 1)
        self.assertEqual(translation, _TRANSLATION4_C)  # not A or B or D
        translation = self._request_translation(_LANGUAGE, None, _KEY4, None)
        self.assertEqual(translation, _TRANSLATION4_A)  # not B or C or D

    def test_two_languages(self):
        """ Check to get the right tranlsation, depending on the language.
        """
        translation = self._request_translation(_LANGUAGE, None, _KEY5, None)
        self.assertEqual(translation, _TRANSLATION5_A)  # and not B
        translation = self._request_translation(_LANGUAGE2, None, _KEY5, None)
        self.assertEqual(translation, _TRANSLATION5_B)  # and not A
