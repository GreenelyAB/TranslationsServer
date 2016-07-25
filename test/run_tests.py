#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Runs unittest.

Automatically adds ../src as a source directory.
If --remote-debug is specified and pydevsrc exists within the project it will
try to connect to the PyDev debug server on the specified IP address.
"""
from argparse import ArgumentParser
from sys import path, argv
from unittest import main


def _connect_to_debug_server(server):
    path.append("../.pydevsrc/")  # @IgnorePep8
    import pydevd  # @UnresolvedImport pylint: disable=import-error
    pydevd.settrace(
        server, stdoutToServer=True, stderrToServer=True, suspend=False)


if __name__ == "__main__":
    path.append("../src")
    parser = ArgumentParser()
    parser.add_argument(
        "-d", "--remote-debug", type=str,
        help="Remote debug server, for example 192.168.33.1")
    args, unknown = parser.parse_known_args()
    if args.remote_debug:
        _connect_to_debug_server(args.remote_debug)
    main(None, argv=argv[:1] + unknown)
