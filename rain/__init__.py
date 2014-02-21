#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Time-stamp: <20-Feb-2014 16:29:56 PST by rich@noir.com>

# Copyright © 2013 - 2014 K Richard Pixley

"""
Class representing disk locations.

.todo: workspace as context manager?
"""

__docformat__ = 'restructuredtext en'

__all__ = [
]

import contextlib
import datetime
import glob
import logging
import os
import shlex
import shutil
import subprocess

class RainException(Exception):
    """Base class for all :py:mod:`rain` exceptions"""
    pass

class WorkAreaAllocationError(RainException):
    """Raised when we can't mkdir a WorkArea"""
    pass

class AllocationError(RainException):
    """Raised when we can't allocate a workspace."""
    pass

class MissingMkfileError(RainException):
    """Raised when creating a WorkingDirectory and we can't find an mk file."""
    pass

class UpdateError(RainException):
    """Raised when updating fails"""
    pass

class BuildError(RainException):
    """Raised when building fails"""
    pass


def isodate():
    """return a single word string representing the time now in iso8609 format"""
    return datetime.datetime.now().isoformat()


class WorkingDirectory(object):
    """
    Class reprenting a working directory.
    """

    mkfilename = 'rain.mk'
    statusfilename = '.rain'

    def __init__(self, logger, name):
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

        mkfilename = os.path.join(os.path.dirname(self.name), self.mkfilename)
        if not os.path.exists(mkfilename):
            logger.error('No %s', os.path.abspath(mkfilename))
            raise MissingMkfileError

    def clear(self):
        """
        Remove any existing directory by our name and mkdir a new one.
        """
        if os.path.exists(self.absname):
            if os.path.isdir(self.absname):
                self.logger.info('removing existing directory \"%s\"', self.absname)
                shutil.rmtree(self.absname)
            else:
                self.logger.info('removing existing file \"%s\"', self.absname)
                os.remove(self.absname)

        self.logger.info('%s - mkdir', self.absname)
        os.mkdir(self.absname)

    @contextlib.contextmanager
    def pushd(self):
        """
        with self.pushd():
            pass
        """
        savedir = os.getcwd()
        os.chdir(self.absname)
        yield

        os.chdir(savedir)

    def status(self, state):
        """write state to our status file"""
        with open(os.path.join(self.absname, self.statusfilename), 'w') as dotrain:
            dotrain.write('{}\n'.format(state))

    def update(self, logfile):
        """bring our source current"""
        retval = self._subcall(logfile, 'update')
        if retval:
            self.logger.error('{} update failed'.format(self.name))
            raise UpdateError

        self.status('updated')
        return not retval

    def build(self, logfile):
        """build us"""
        retval = self._subcall(logfile, 'build')

        if retval:
            self.logger.error('{} build failed'.format(self.name))
            raise BuildError

        self.status('built')
        return not retval

    def poll(self, logfile):
        """check to see whether this directory is up to date with source control"""
        retval = self._subcall(logfile, 'poll')
        self.logger.info('{} polled: {}'.format(self.name, retval))
        return not retval

    def _subcall(self, logfile, target):
        """call mkfile on target"""
        cmd = '{} {}'.format(os.path.join('.', self.mkfilename), target)
        self.logger.info('%s - cd && %s', self.name, cmd)
        return subprocess.call(shlex.split(cmd), stdout=logfile, stderr=logfile, cwd=self.absname)


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
                raise WorkAreaAllocationError

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
    def pushd(self):
        """
        with pushd():
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

            with working_directory.pushd():
                retval |= working_directory.update(logfile)

                if retval:
                    return retval

                working_directory.status('incomplete')
                retval |= working_directory.build(logfile)

            if not retval:
                self.current_working_directory = working_directory.name

        return retval


