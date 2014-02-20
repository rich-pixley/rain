#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Time-stamp: <19-Feb-2014 16:59:22 PST by rich@noir.com>

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
import glob
import logging
import os
import shlex
import shutil
import subprocess

import rain

__docformat__ = "restructuredtext en"

REMOVAL_CMDS = ['remove', 'rm', 'delete', 'del']

@contextlib.contextmanager
def pushdir(newdir):
    """
    with pusdir(newdir):
        pass
    """
    savedir = os.getcwd()
    os.chdir(newdir)
    yield

    os.chdir(savedir)

def isodate():
    """return a single word string representing the time now in iso8609 format"""
    return datetime.datetime.now().isoformat()

class WorkingDirectory(object):
    """
    Class reprenting a working directory.
    """

    mkfile = 'rain.mk'

    def __init__(self, logger, name):
        self.logger = logger
        self.name = name

        if not os.path.exists(os.path.join(self.name, '../', self.mkfile)):
            logger.error('No %s', self.mkfile)
            raise rain.MissingMkfileError

    def clear(self):
        """
        Remove any existing directory by our name and mkdir a new one.
        """
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
        """
        with self.pushdir():
            pass
        """
        savedir = os.getcwd()
        os.chdir(self.name)
        yield

        os.chdir(savedir)

    def status(self, state):
        """write state to our status file"""
        with open(os.path.join(self.name, '.rain'), 'w') as dotrain:
            dotrain.write('{}\n'.format(state))

    def populate(self, logfile):
        """fill us with source from wherever"""
        retval = self._subcall(logfile, 'populate')
        if retval:
            self.logger.error('{} populate failed'.format(self.name))
            raise PopulationException

        self.status('populated')
        return not retval

    def build(self, logfile):
        """build us"""
        retval = self._subcall(logfile, 'build')

        if retval:
            self.logger.error('{} build failed'.format(self.name))
            raise BuildException

        self.status('built')
        return not retval

    def poll(self, logfile):
        """check to see whether this directory is up to date with source control"""
        retval = self._subcall(logfile, 'poll')
        self.logger.info('{} polled: {}'.format(self.name, retval))
        return not retval

    def _subcall(self, logfile, target):
        """call mkfile on target"""
        cmd = '{} {}'.format(self.mkfile, target)
        self.logger.info('%s - cd && %s', self.name, cmd)
        return subprocess.call(shlex.split(cmd), stdout=logfile, stderr=logfile)


class WorkArea(object):
    """
    A WorkArea represents a place in the file system which will contain
    WorkingDirectory's.  It also contains a rain.mk and some state.

    At any given point in time, it may also have a current_working_directory.

    The state of a WorkArea resides entirely on disk.
    """

    current_working_directory_file = '.rain-current_working_directory'

    def __init__(self, logger, name='.'):
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
                logger.error('FATAL: WorkArea %s exists and is not a directory'.format(self.name))
                raise rain.WorkAreaAllocationError

    @property
    def current_working_directory(self): # property/accessor
        """accesssor for current_working_directory"""
        if os.path.exists(self.current_working_directory_file):
            with open(self.current_working_directory_file, 'r') as ifile:
                return ifile.read().strip()
        else:
            return None

    @current_working_directory.setter
    def current_working_directory(self, new):
        """setter for current_working_directory"""
        with open(self.current_working_directory_file, 'w') as ofile:
            ofile.write(new)

        # pylint: disable=W0201
        self._current_working_directory = new
        # pylint: enable=W0201

    @current_working_directory.deleter
    def current_working_directory(self):
        """deleter for current_working_directory"""
        try:
            os.remove(self.current_working_directory_file)
        except OSError:
            if not os.path.exists(self.current_working_directory_file):
                pass
            else:
                self.logger.error('FATAL: failed to remove {}'.format(self.current_working_directory_file))
                raise

    @contextlib.contextmanager
    def pushdir(self):
        """
        with pushdir():
            pass
        """
        savedir = os.getcwd()
        os.chdir(self.absname)
        yield

        os.chdir(savedir)


    @staticmethod
    def raindirs():
        """return a list of working directories"""
        return sorted([os.path.dirname(d) for d in glob.glob('*/.rain')])

    def keep(self, count):
        """possibly remove some working directories"""

        dirs = self.raindirs()
        if count == 0:
            for directory in dirs:
                self.logger.info('%s removing...', directory)
                shutil.rmtree(directory)
                self.logger.debug('%s removed.', directory)
        else:
            for directory in dirs[:-count]:
                self.logger.info('%s removing...', directory)
                shutil.rmtree(directory)
                self.logger.debug('%s removed.', directory)

    def new_working_directory(self):
        """Create a new working directory"""
        return WorkingDirectory(self.logger, isodate())

    def do_pass(self, keep=-1):
        """do a buildpass"""
        retval = False # True on error

        if keep != -1: # minus one means "keep everything"
            self.keep(keep)

        with open('Log-' + isodate(), 'w') as logfile:
            working_directory = self.current_working_directory

            if not working_directory:
                working_directory = self.new_working_directory()
                working_directory.clear()
                working_directory.status('fresh')

            with working_directory.pushdir():
                retval |= working_directory.update(logfile)

                if retval:
                    return retval

                working_directory.status('incomplete')
                retval |= working_directory.build(logfile)

            if not retval:
                self.current_working_directory = working_directory.name

        return retval


class PopulationException(Exception):
    """Raised when populating fails"""
    pass

class BuildException(Exception):
    """Raised when building fails"""
    pass

def main():
    """main"""
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
        stuff = '\n'.join(area.raindirs())
        if stuff:
            print(stuff)

    elif options.action in ['keep']:
        area.keep(options.count)

    # elif options.action in ['poll']:
    #     return area.poll(logfile)

    elif options.action in REMOVAL_CMDS:
        for directory in area.raindirs()[:options.count]:
            shutil.rmtree(directory)

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
                                 'poll'] + REMOVAL_CMDS)

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
