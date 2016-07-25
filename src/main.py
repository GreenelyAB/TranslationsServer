#!/usr/bin/env python
# -*- coding: utf-8 -*-
from argparse import ArgumentParser
from sys import path

import config  # setup logging!
from translations_server import run


def _connect_to_debug_server(server):
    path.append("../.pydevsrc/")  # @IgnorePep8
    import pydevd  # @UnresolvedImport pylint: disable=import-error
    pydevd.settrace(
        server, stdoutToServer=True, stderrToServer=True, suspend=False)


if __name__ == "__main__":
    _parser = ArgumentParser()
    _parser.add_argument(
        "-p", "--port", type=int, help="Server port number",
        default=config.DEFAULT_PORT)
    _parser.add_argument(
        "-d", "--remote-debug", type=str,
        help="Remote debug server, for example 192.168.33.1")
    _args, _ = _parser.parse_known_args()
    if _args.remote_debug:
        _connect_to_debug_server(_args.remote_debug)
    run(_args.port)
