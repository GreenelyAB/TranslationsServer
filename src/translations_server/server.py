# -*- coding: utf-8 -*-
from logging import getLogger
from threading import Thread

from zmq import REQ, REP, Poller, POLLIN, Context, ROUTER, DEALER, proxy

import config
from translations_server.db import get_translation
from translations_server.lib import db


_LOG = getLogger(__name__)

_ENCODING = "utf-8"

_REQUEST_ENDPOINT = "inproc://requests"

_SYNC_ENDPOINT = "inproc://sync"


def _translate(lang, country, *key_plural_pairs):
    """ Generator: get translations from the DB. """
    # Group each two elements together to key and plural tuples.
    key_plural_pairs = zip(  # 1, 2, 3, 4, ... -> (1, 2), (3, 4), ...
        key_plural_pairs[::2], key_plural_pairs[1::2])
    for key, plural in key_plural_pairs:
        plural = int(plural) if plural else None
        yield get_translation(lang, country, key, plural) or key


def _handle_request(parts):
    """ Handle one translation request, translate and return the result.

    In and out-puts are bytes.

    :param parts: Translation fields:
        - language
        - country or `""`
        - on or more pairs of key and plural form
    :type parts: [bytes]
    :return: The translations or `[b""]` if there was a encoding or format
        error.
    :rtype: [bytes] or [b""]
    """
    translations = [b""]  # error
    try:
        parts = [p.decode(_ENCODING) for p in parts]
    except UnicodeDecodeError:
        _LOG.exception("Decoding error", extra={"encoding": _ENCODING})
    else:
        if len(parts) < 4 or len(parts) % 2:
            _LOG.warning("Wrong count of arguments.")
        else:
            lang, country = parts[:2]
            try:
                translations = [
                    t.encode(_ENCODING)
                    for t in _translate(lang, country, *parts[2:])]
            except UnicodeEncodeError:
                _LOG.exception(
                    "Could not encode translation!",
                    extra={"encoding": _ENCODING})
            finally:
                # Close DB connection if any was opened.
                db.close()
    return translations


def _handle_requests(context):
    """ This is supposed to run as a background thread.

    It listens for translation requests and answers them until a message is
    arrived on the sync socket, whereupon the function (thread) ends.

    :type context: zmq.Context
    """
    sync_socket = context.socket(REQ)
    sync_socket.connect(_SYNC_ENDPOINT)
    requests_socket = context.socket(REP)
    requests_socket.connect(_REQUEST_ENDPOINT)

    _LOG.debug("Synchronizing worker")
    sync_socket.send(b"")
    sync_socket.recv()
    sync_socket.send(b"")

    keep_running = True
    poller = Poller()
    poller.register(requests_socket, POLLIN)
    poller.register(sync_socket, POLLIN)
    _LOG.debug("Running worker")
    while keep_running:
        sockets = dict(poller.poll())
        if requests_socket in sockets:
            try:
                response = _handle_request(requests_socket.recv_multipart())
            except Exception:  # pylint: disable=broad-except
                _LOG.critical("Handler crashed!", exc_info=True)
                response = [b""]
            requests_socket.send_multipart(response)
        if sync_socket in sockets:
            sync_socket.recv()
            keep_running = False
    _LOG.debug("Terminating worker")


def _start_workers(context, sync_socket, count, timeout=None):
    """
    :type context: zmq.Context
    :type sync_socker: zmq.Socket
    :type count: int
    :param timeout: Timeout for waiting for worker messages, in milliseconds.
    :type timeout: float
    """
    _LOG.debug("Starting workers...")
    worker_threads = [
        Thread(
            target=_handle_requests, name="worker {}".format(i),
            args=(context, ))
        for i in range(count)]
    for thread in worker_threads:
        thread.start()
    _LOG.debug("Synchronizing workers...")
    poller = Poller()
    poller.register(sync_socket, POLLIN)
    worker_identities = []
    for _ in worker_threads:
        sockets = dict(poller.poll(timeout=timeout))
        if sync_socket in sockets:
            worker_identities.append(sync_socket.recv_multipart()[0])
        else:
            raise RuntimeError("Worker did not respond in time.")
    for worker_identity in worker_identities:
        sync_socket.send_multipart([worker_identity, b"", b""])
    for _ in worker_identities:
        sockets = dict(poller.poll(timeout=timeout))
        if sync_socket in sockets:
            sync_socket.recv_multipart()
        else:
            raise RuntimeError("Worker did not respond in time.")
    _LOG.debug("Workers synchronized.")
    return worker_threads, worker_identities


def _shut_down_workers(
        sync_socket, worker_threads, worker_identities, timeout=None):
    """
    :type sync_socker: zmq.Socket
    :type worker_threads: [threading.Thread]
    :type worker_identities: [bytes]
    :param timeout: Timeout for waiting for worker threads, in seconds.
    :type timeout: float
    """
    _LOG.debug("Terminating workers...")
    for worker_identity in worker_identities:
        sync_socket.send_multipart([worker_identity, b"", b""])
    for i, thread in enumerate(worker_threads):
        thread.join(timeout=timeout)
        if thread.is_alive():
            raise RuntimeError("Worker {} did not terminate.".format(i))
    _LOG.debug("Workers terminated.")


def run(port):
    """ Run a translations server at a spesific port.

    It always listens on all available network devices!
    """
    context = Context(1)
    sync_socket = context.socket(ROUTER)
    sync_socket.bind(_SYNC_ENDPOINT)
    frontend = context.socket(ROUTER)
    frontend.bind("tcp://*:{}".format(port))
    # Socket facing services
    backend = context.socket(DEALER)
    backend.bind(_REQUEST_ENDPOINT)
    try:
        worker_threads, worker_identities = _start_workers(
            context, sync_socket, config.WORKERS, 1000)
        _LOG.debug("Running device...")
        try:
            proxy(frontend, backend)
        except KeyboardInterrupt:
            print("\rShutting down...")
        frontend.close()
        frontend = None
        _shut_down_workers(sync_socket, worker_threads, worker_identities, 5)
    finally:
        if frontend is not None:
            frontend.close()
        backend.close()
        sync_socket.close()
    _LOG.debug("Done")
