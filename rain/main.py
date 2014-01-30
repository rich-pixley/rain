#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Time-stamp: <29-Jan-2014 19:47:27 PST by rich@noir.com>

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

class WorkArea:
    def __init__(self, logger):
        self.logger = logger

    @staticmethod
    def raindirs():
        return sorted([os.path.dirname(d) for d in glob.glob('*/.rain')])

    def keep(self, count):
        dirs = self.raindirs()
        if count == 0:
            for dir in dirs:
                self.logger.info('%s removing...', dir)
                shutil.rmtree(dir)
                self.logger.debug('%s removed.', dir)
        else:
            for dir in dirs[:-count]:
                self.logger.info('%s removing...', dir)
                shutil.rmtree(dir)
                self.logger.debug('%s removed.', dir)

    def new_working_directory(self, buildscript):
        return WorkingDirectory(self.logger, isodate(), buildscript)

class PopulationException(Exception):
    pass

class BuildException(Exception):
    pass

class WorkingDirectory:
    def __init__(self, logger, name, buildscript):
        self.logger = logger
        self.name = name
        self.buildscript = buildscript

    def clear(self):
        if os.path.exists(self.name):
            if os.path.isdir(self.name):
                self.logger.info('removing existing directory named \"%s\"', self.name)
                shutil.rmtree(self.name)
            else:
                self.logger.info('removing existing file named \"%s\"', self.name)
                os.remove(self.name)

        self.logger.info('%s - mkdir', self.name)
        os.mkdir(self.name)

    @contextlib.contextmanager
    def pushdir(self):
        savedir = os.getcwd()
        os.chdir(self.name)
        yield

        os.chdir(savedir)

    def status(self, state):
        with open('.rain', 'w') as dotrain:
            dotrain.write('{}\n'.format(state))

    def populate(self, logfile):
        retval = self.subcall(logfile, 'populate')
        if retval:
            self.logger.error('{} populate failed'.format(self.name))
            raise PopulationException

        self.status('populated')
        return not retval

    def build(self, logfile):
        retval = self.subcall(logfile, 'build')

        if retval:
            self.logger.error('{} build failed'.format(self.name))
            raise BuildException

        self.status('built')
        return not retval

    def subcall(self, logfile, target):
        cmd = '{} {}'.format(self.buildscript, target)
        self.logger.info('%s - cd && %s', self.name, cmd)
        return subprocess.call(shlex.split(cmd), stdout=logfile, stderr=logfile)


def main():
    logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%Y-%m-%dT%H:%M:%S%z')
    logger = logging.getLogger()

    options = _parse_args()

    log_level = logging.INFO

    if options.verbose > 0:
        log_level = logging.DEBUG

    logger.setLevel(log_level)

    area = WorkArea(logger)

    if options.action in ['build']:

        # do stuff
        counter = options.count
        mkfile = 'rain.mk'

        while options.count == 0 or counter > 0:
            counter -= 1

            if options.keep != -1: # minus one means "keep everything"
                area.keep(options.keep)

            wd = area.new_working_directory('../{}'.format(mkfile))
            wd.clear()

            if not os.path.exists(mkfile):
                logger.error('No %s', mkfile)
                return 1

            with wd.pushdir():
                wd.status('incomplete')
                with open('Log-' + isodate(), 'w') as logfile:
                    retval = wd.populate(logfile)

                    if retval:
                        retval = wd.build(logfile)

        return retval

    elif options.action in ['ls']:
        stuff = '\n'.join(raindirs())
        if stuff:
            print(stuff)

    elif options.action in ['keep']:
        area.keep(options.count)

    elif options.action in removal_cmds:
        for dir in area.raindirs()[:options.count]:
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
