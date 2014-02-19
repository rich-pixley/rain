#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Time-stamp: <18-Feb-2014 18:07:59 PST by rich@mito>

# Copyright © 2013 - 2014 K Richard Pixley

"""
Shell callable driver for :py:mod:`rain`.

fixme: need incremental builds before we can poll

fixme: need a mechanism for working directory name normalization for
builds that bolt full path names.

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

def isodate():
    return datetime.datetime.now().isoformat()

class WorkingDirectory:
    mkfile = 'rain.mk'

    def __init__(self, logger, name):
        self.logger = logger
        self.name = name

        if not os.path.exists(os.path.join(self.name, '../', mkfile)):
            logger.error('No %s', mkfile)
            return 1


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

    def poll(self, logfile):
        retval = self.subcall(logfile, 'poll')
        self.logger.info('{} polled: {}'.format(self.name, retval))
        return not retval

    def subcall(self, logfile, target):
        cmd = '{} {}'.format(self.mkfile, target)
        self.logger.info('%s - cd && %s', self.name, cmd)
        return subprocess.call(shlex.split(cmd), stdout=logfile, stderr=logfile)


class WorkArea:
    current_wd_file = '.rain-current_wd'

    def __init__(self, logger, name='.'):
        """
        A WorkArea represents a place in the file system which will contain
        WorkingDirectory's.  It also contains a rain.mk and some state.

        At any given point in time, it may also have a current_wd.

        The state of a WorkArea resides entirely on disk.
        """

        self.logger = logger
        self.name = name

        # relname isn't dynamic because it's dependent on cwd.
        name = os.path.normpath(name)
        if os.path.isabs(name):
            self.absname = name
            self.relname = os.path.relpath(name)
        else:
            self.absname = os.path.abspath(name)
            self.relname = name

        try:
            os.mkdir(name)

        except OSError:
            if not os.path.isdir(name):
                logger.error('FATAL: WorkArea %s exists and is not a'
                             + ' directory'.format(self.name))  
                raise WorkAreaAllocationError

    @property
    def current_wd(self): # property/accessor
        if os.path.exists(self.current_wd_file):
            with open(self.current_wd_file, 'rt') as ifile:
                return ifile.read().strip()
        else:
            return None

    @current_wd.setter
    def current_wd(self, new):
        with open(self.current_wd_file, 'wt') as ofile:
            ofile.write(new)

        self._current_wd = new
    
    @current_wd.deleter
    def current_wd(self):
        try:
            os.remove(self.current_wd_file)
        except OSError:
            if not os.path.exists(self.current_wd_file):
                pass
            else:
                logger.error('FATAL: failed to remove'
                             + ' {}'.format(self.current_wd_file))
                raise

    @contextlib.contextmanager
    def pushdir(self):
        savedir = os.getcwd()
        os.chdir(self.absname)
        yield

        os.chdir(savedir)


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

    def new_working_directory(self):
        return WorkingDirectory(self.logger, isodate())

    def do_pass(self, keep=-1):
        retval = False # True on error

        if keep != -1: # minus one means "keep everything"
            self.keep(keep)

        with open('Log-' + isodate(), 'w') as logfile:
            wd = area.current_wd

            if not wd:
                wd = area.new_working_directory()
                wd.clear()
                wd.status('fresh')

            with wd.pushdir():
                retval |= wd.update(logfile)

                if retval:
                    return retval

                wd.status('incomplete')
                retval |= wd.build(logfile)

            if not retval:
                area.current_wd = wd.name

        return retval

class PopulationException(Exception):
    pass

class BuildException(Exception):
    pass

def main():
    logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%Y-%m-%dT%H:%M:%S%z')
    logger = logging.getLogger()

    options = _parse_args()

    log_level = logging.INFO

    if options.verbose > 0:
        log_level = logging.DEBUG

    logger.setLevel(log_level)

    area = WorkArea(logger)

    retval = False # True on error

    if options.action in ['build']:
        counter = options.count
        while options.count == 0 or counter > 0:
            retval |= area.do_pass(options.keep)
            counter -= 1

    elif options.action in ['ls']:
        stuff = '\n'.join(raindirs())
        if stuff:
            print(stuff)

    elif options.action in ['keep']:
        area.keep(options.count)

    elif options.action in ['poll']:
        return area.poll(logfile)

    elif options.action in removal_cmds:
        for dir in area.raindirs()[:options.count]:
            shutil.rmtree(dir)

    return retval


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
                                 'keep',
                                 'poll'] + removal_cmds)

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
