#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Time-stamp: <21-Feb-2014 12:41:53 PST by rich@noir.com>

# Copyright © 2013 - 2014 K Richard Pixley

"""
Class representing disk locations.
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

class MissingCtrlFileError(RainException):
    """Raised when we can't find control file."""
    pass

class NoXCtrlFileError(RainException):
    """Raised when control file is not executable."""
    pass

class UpdateError(RainException):
    """Raised when updating fails"""
    pass

class BuildError(RainException):
    """Raised when building fails"""
    pass

class StateRemovalError(Exception):
    """Raised when we fail to remove a state file"""
    pass

def isodate():
    """return a single word string representing the time now in iso8609 format"""
    return datetime.datetime.now().isoformat()


class Statefull(object):
    class _StateDirectory(object):
        """_StateDirectory"""

        def __init__(self, dirname):
            object.__setattr__(self, 'dirname', os.path.abspath(os.path.normpath(dirname)))

        def mkstatedir(self):
            try:
                os.mkdir(self.dirname)
            except OSError:
                if not os.path.isdir(self.dirname):
                    raise

        def fname(self, name):
            """fname"""
            return os.path.join(self.dirname, name)

        def __getattr__(self, name):
            """accesssor"""
            fname = self.fname(name)

            if os.path.exists(fname):
                with open(fname, 'r') as ifile:
                    return ifile.read().strip()
            else:
                return None

        def __setattr__(self, name, newval):
            """setter"""
            fname = self.fname(name)

            with open(fname, 'w') as ofile:
                ofile.write(newval)

        def __deleter__(self, name):
            """deleter"""
            fname = self.fname(name)

            try:
                os.remove(fname)

            except OSError:
                if not os.path.exists(fname):
                    pass
                else:
                    raise StateRemovalError

            try:
                os.rmdir(self.dirname)

            except OSError:
                pass

    def __init__(self, dirname):
        self.state = self._StateDirectory(dirname)

    def mkstatedir(self):
        self.state.mkstatedir()

    @classmethod
    def statevalue(cls, name):
        return property(lambda self: self.state.__getattr__(name),
                        lambda self, newval: self.state.__setattr__(name, newval),
                        lambda self: self.state.__delattr__(name),
                        'generated property')


class WorkingDirectory(Statefull):
    """
    Class reprenting a working directory.
    """

    statedirname = '.rain-work'

    def __init__(self, logger, name, ctrlfilename):
        self.logger = logger
        self.name = name
        self.ctrlfilename = ctrlfilename

        # relname isn't dynamic because it's dependent on cwd.
        name = os.path.normpath(name)
        if os.path.isabs(name):
            self.absname = name
            self.relname = os.path.relpath(name)
        else:
            self.absname = os.path.abspath(name)
            self.relname = name

        super().__init__(os.path.join(self.absname, self.statedirname))

        if not os.path.isdir(self.absname):
           self.clear()

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
        self.mkstatedir()

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

    def update(self, logfile):
        """bring our source current"""
        retval = self._subcall(logfile, 'update')
        if retval:
            self.logger.error('{} update failed'.format(self.name))
            raise UpdateError

        self.status = 'updated'
        return not retval

    def build(self, logfile):
        """build us"""
        retval = self._subcall(logfile, 'build')

        if retval:
            self.logger.error('{} build failed'.format(self.name))
            raise BuildError

        self.status = 'built'
        return not retval

    def poll(self, logfile):
        """check to see whether this directory is up to date with source control"""
        retval = self._subcall(logfile, 'poll')
        self.logger.info('{} polled: {}'.format(self.name, retval))
        return not retval

    def _subcall(self, logfile, target):
        """call ctrlfile on target"""

        # FIXME: this should probably check for executability but I
        # don't seen an easy call for that.

        if not os.path.exists(self.ctrlfilename):
            raise MissingCtrlFileError

        if not os.access(self.ctrlfilename, os.X_OK,
                         effective_ids=os.access in os.supports_effective_ids):
            raise NoXCtrlFileError

        cmd = '{} {}'.format(os.path.join('.', self.ctrlfilename), target)
        self.logger.info('%s - cd && %s', self.name, cmd)
        return subprocess.call(shlex.split(cmd), stdout=logfile, stderr=logfile, cwd=self.absname)

WorkingDirectory.status = WorkingDirectory.statevalue('status')


class WorkArea(Statefull):
    """
    A WorkArea represents a place in the file system which will contain
    WorkingDirectory's.  It also contains a rain.mk and some state.

    At any given point in time, it may also have a cwd.

    The state of a WorkArea resides entirely on disk.
    """

    statedirname = '.rain-area'

    def __init__(self, logger, name='.', ctrlfilename='rain.mk'):
        self.logger = logger
        self.name = name

        # Relname isn't dynamic because it's dependent on cwd.
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

        super().__init__(os.path.join(self.absname, self.statedirname))

        self.ctrlfilename = os.path.join(self.absname, ctrlfilename)

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

    @property
    def wds(self):
        """return a list of known working directories"""
        _wds = self._wds
        if _wds is None:
            _wds = ''
        return sorted(_wds.strip().split('\n'))

    @wds.setter
    def wds(self, newval):
        """wds setter"""
        self._wds = ''.join([x + '\n' for x in newval])

    def new_working_directory(self):
        """Create a new working directory"""
        name = isodate()
        absname = os.path.normpath(os.path.join(self.absname, name))
        newwd = WorkingDirectory(self.logger, absname, self.ctrlfilename)
        self.wds += [name]
        return newwd

    def keep(self, count):
        """possibly remove some working directories"""

        dirs = self.wds()
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

    def do_pass(self, keep=-1):
        """do a buildpass"""
        retval = False # True on error

        if keep != -1: # minus one means "keep everything"
            self.keep(keep)

        with open('Log-' + isodate(), 'w') as logfile:
            wdir = self.cwd

            if not wdir:
                wdir = self.new_working_directory()
                wdir.clear()
                wdir.status = 'fresh'

            with wdir.pushd():
                retval |= wdir.update(logfile)

                if retval:
                    return retval

                wdir.status('incomplete')
                retval |= wdir.build(logfile)

            if not retval:
                self.cwd = wdir.name

        return retval

WorkArea.cwd = WorkArea.statevalue('cwd')
WorkArea._wds = WorkArea.statevalue('wds')

