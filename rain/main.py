#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Time-stamp: <26-Jan-2014 21:01:50 PST by rich@noir.com>

# Copyright © 2013 - 2014 K Richard Pixley

"""
Shell callable driver for :py:mod:`rain`.
"""

import argparse
import fnmatch
import logging
import os
import re
import contextlib
import subprocess
import shlex
import shutil

import rain

__docformat__ = "restructuredtext en"

@contextlib.contextmanager
def pushdir(newdir):
    savedir = os.getcwd()
    os.chdir(newdir)
    yield

    os.chdir(savedir)

# class EmacsBuild:
#     @staticmethod
#     def build(workspace):
#         try:
#             with pushdir(workspace.name):
#                 subprocess.check_call(shlex.split('tar xfJ /home/rich/local/src/emacs-24.3.tar.xz'))
#                 with pushdir('emacs-24.3'):
#                     subprocess.check_call(shlex.split('./configure --with-x-toolkit=no --with-xpm=no --with-jpeg=no --with-png=no --with-gif=no --with-tiff=no'))
#                     subprocess.check_call(shlex.split('time make -j4'))

#         except:
#             return False

#         return True

def main():
    # location = Location('.')
    # workspace = location.next_workspace()

    logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%Y-%m-%dT%H:%M:%S%z')
    logger = logging.getLogger()

    options = _parse_args()

    log_level = logging.INFO

    if options.verbose > 0:
        log_level = logging.DEBUG

    logger.setLevel(log_level)

    # do stuff

    ws = 'WorkSpace'

    counter = options.count

    while options.count == 0 or counter > 0:
        counter -= 1

        if os.path.exists(ws):
            if os.path.isdir(ws):
                logger.info('removing existing directory named \"%s\"', ws)
                shutil.rmtree(ws)
            else:
                logger.info('removing existing file named \"%s\"', ws)
                os.remove(ws)

        logger.info('mkdir %s', ws)
        os.mkdir(ws)

        bldcmd = '../rain.mk build'

        with open('Output', 'w') as output:
            with pushdir(ws):
                logger.info('cd %s && %s', ws, bldcmd)
                retval = subprocess.call(shlex.split(bldcmd), stdout=output, stderr=output)

        logger.info('build %s', 'failed' if retval else 'succeeded')

    return retval

def _parse_args():
    """
    Parses the command line arguments.

    :return: Namespace with arguments.
    :rtype: Namespace
    """
    parser = argparse.ArgumentParser(description='rain - a new sort of automated builder.')
    
    # parser.add_argument('thingtodo', help='what shall we do?')

    parser.add_argument('-c', '--count', type=int, default=1,
                        help='number of times to iterate. [default: %(default)s]')

    parser.add_argument('-v', '--verbose', action='count', default=0, help='Be more verbose. (can be repeated)')

    parser.add_argument('--version', default=False, action='store_true',
                        help='print version number and exit. [default: %(default)s]')

    return parser.parse_args()

if __name__ == '__main__':
    main()
