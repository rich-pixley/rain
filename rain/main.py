#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Time-stamp: <29-Jan-2014 17:35:56 PST by rich@noir.com>

# Copyright © 2013 - 2014 K Richard Pixley

"""
Shell callable driver for :py:mod:`rain`.
"""

import argparse
import contextlib
import datetime
import fnmatch
import glob
import logging
import os
import re
import shlex
import shutil
import subprocess

import rain

__docformat__ = "restructuredtext en"

removal_cmds = ['remove', 'rm', 'delete', 'del']

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

def isodate():
    return datetime.datetime.now().isoformat()

def WSiso():
    return isodate() # %Y-%m-%dT%H:%M:%S%z

def raindirs():
    return sorted([os.path.dirname(d) for d in glob.glob('*/.rain')])

def WSkeep(logger, count):
    dirs = raindirs()
    if count == 0:
        for dir in dirs:
            logger.info('%s removing...', dir)
            shutil.rmtree(dir)
            logger.debug('%s removed.', dir)
    else:
        for dir in dirs[:-count]:
            logger.info('%s removing...', dir)
            shutil.rmtree(dir)
            logger.debug('%s removed.', dir)

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

    if options.action in ['build']:

        # do stuff
        counter = options.count
        mkfile = 'rain.mk'

        while options.count == 0 or counter > 0:
            counter -= 1

            if options.keep != -1: # minus one means "keep everything"
                WSkeep(logger, options.keep)

            ws = WSiso()

            if os.path.exists(ws):
                if os.path.isdir(ws):
                    logger.info('removing existing directory named \"%s\"', ws)
                    shutil.rmtree(ws)
                else:
                    logger.info('removing existing file named \"%s\"', ws)
                    os.remove(ws)

            logger.info('%s - mkdir', ws)
            os.mkdir(ws)

            if os.path.exists(mkfile):
                bldcmd = '../{} build'.format(mkfile)
            else:
                logger.error('No %s', mkfile)
                return 1

            with pushdir(ws):
                with open('.rain', 'w') as dotrain:
                    dotrain.write('incomplete\n')

                with open('Log-' + isodate(), 'w') as output:
                    logger.info('%s - cd && %s', ws, bldcmd)
                    retval = subprocess.call(shlex.split(bldcmd), stdout=output, stderr=output)

                with open('.rain', 'w') as dotrain:
                    dotrain.write('failure\n' if retval else 'success\n')

            logger.info('%s - %s', ws, 'failed' if retval else 'succeeded')

        return retval

    elif options.action in ['ls']:
        stuff = '\n'.join(raindirs())
        if stuff:
            print(stuff)

    elif options.action in ['keep']:
        WSkeep(logger, options.count)

    elif options.action in removal_cmds:
        for dir in raindirs()[:options.count]:
            shutil.rmtree(dir)

    return False


def _parse_args():
    """
    Parses the command line arguments.

    :return: Namespace with arguments.
    :rtype: Namespace
    """
    parser = argparse.ArgumentParser(description='rain - a new sort of automated builder.')
    
    parser.add_argument('action', help='what shall we do?', default='build', nargs='?',
                        choices=['build',
                                 'ls',
                                 'keep'] + removal_cmds)

    parser.add_argument('-c', '--count', type=int, default=1,
                        help='a count of items on which to operate. [default: %(default)s]')

    parser.add_argument('--keep', type=int, default=-1,
                        help='how many builds should we keep around? [default: %(default)s]')

    parser.add_argument('-v', '--verbose', action='count', default=0, help='Be more verbose. (can be repeated)')

    parser.add_argument('--version', default=False, action='store_true',
                        help='print version number and exit. [default: %(default)s]')

    return parser.parse_args()

if __name__ == '__main__':
    main()
