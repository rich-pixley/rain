#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Time-stamp: <21-Feb-2014 12:41:15 PST by rich@noir.com>

# Copyright © 2013 - 2014 K Richard Pixley

"""
tests
"""

__docformat__ = 'restructuredtext en'

import logging
import os
import shutil
import tempfile
import unittest
import sys
import subprocess
import contextlib

import nose
from nose.tools import assert_false, assert_equal, raises

import rain

logger = logging.getLogger()

verbose_logging = False
if verbose_logging:
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    logger.addHandler(handler)

class StateDirectory(unittest.TestCase):
    def setUp(self):
        self.tdir = tempfile.mkdtemp(dir='tests')
        shutil.rmtree(self.tdir)
        self.state = rain.Statefull._StateDirectory(self.tdir)
        self.state.mkstatedir()

    def tearDown(self):
        shutil.rmtree(self.tdir)

    def test_persistence(self):
        self.assertEquals(self.state.one, None)
        self.assertEquals(self.state.two, None)
        self.assertEquals(self.state.three, None)

        self.state.one = 'first'
        self.assertEquals(self.state.one, 'first')
        self.assertEquals(self.state.two, None)
        self.assertEquals(self.state.three, None)

        self.state.two = 'second'
        self.assertEquals(self.state.one, 'first')
        self.assertEquals(self.state.two, 'second')
        self.assertEquals(self.state.three, None)

        self.state.three = 'third'
        self.assertEquals(self.state.one, 'first')
        self.assertEquals(self.state.two, 'second')
        self.assertEquals(self.state.three, 'third')

        self.state = rain.Statefull._StateDirectory(self.tdir)
        self.assertEquals(self.state.one, 'first')
        self.assertEquals(self.state.two, 'second')
        self.assertEquals(self.state.three, 'third')

class Statefull(unittest.TestCase):
    class Mystate(rain.Statefull):
        pass

    Mystate.one = Mystate.statevalue('one')
    Mystate.two = Mystate.statevalue('two')
    Mystate.three = Mystate.statevalue('three')

    def setUp(self):
        self.tdir = tempfile.mkdtemp(dir='tests')
        shutil.rmtree(self.tdir)
        self.mystate = self.Mystate(self.tdir)
        self.mystate.mkstatedir()

    def tearDown(self):
        shutil.rmtree(self.tdir)

    def test_statevalue(self):
        self.assertEquals(self.mystate.one, None)
        self.assertEquals(self.mystate.two, None)
        self.assertEquals(self.mystate.three, None)

        self.mystate.one = 'first'
        self.assertEquals(self.mystate.one, 'first')
        self.assertEquals(self.mystate.two, None)
        self.assertEquals(self.mystate.three, None)

        # persistence check
        self.mystate = self.Mystate(self.tdir)
        self.assertEquals(self.mystate.one, 'first')
        self.assertEquals(self.mystate.two, None)
        self.assertEquals(self.mystate.three, None)

        self.mystate.two = 'second'
        self.assertEquals(self.mystate.one, 'first')
        self.assertEquals(self.mystate.two, 'second')
        self.assertEquals(self.mystate.three, None)

        # persistence check
        self.mystate = self.Mystate(self.tdir)
        self.assertEquals(self.mystate.one, 'first')
        self.assertEquals(self.mystate.two, 'second')
        self.assertEquals(self.mystate.three, None)

        self.mystate.three = 'third'
        self.assertEquals(self.mystate.one, 'first')
        self.assertEquals(self.mystate.two, 'second')
        self.assertEquals(self.mystate.three, 'third')

        # persistence check
        self.mystate = self.Mystate(self.tdir)
        self.assertEquals(self.mystate.one, 'first')
        self.assertEquals(self.mystate.two, 'second')
        self.assertEquals(self.mystate.three, 'third')

class isodate(unittest.TestCase):
    def test_isodate(self):
        self.assertEqual(len(rain.isodate()), 26)

bintrueprog = '/bin/true'
usrbintrueprog = '/usr/bin/true'

if os.access(bintrueprog, os.X_OK):
    trueprog = bintrueprog
elif os.access(usrbintrueprog, os.X_OK):
    trueprog = usrbintrueprog
else:
    raise NotImplementedError

binfalseprog = '/bin/false'
usrbinfalseprog = '/usr/bin/false'

if os.access(binfalseprog, os.X_OK):
    falseprog = binfalseprog
elif os.access(usrbinfalseprog, os.X_OK):
    falseprog = usrbinfalseprog
else:
    raise NotImplementedError

class WorkingDirectory(unittest.TestCase):
    ctrlstub = trueprog

    def setUp(self):
        self.tdir = tempfile.mkdtemp(dir='tests')
        self.assertTrue(os.path.isdir(self.tdir))

        self.wdir = rain.WorkingDirectory(logger, self.tdir, self.ctrlstub)
        print('clearing')
        self.wdir.clear()

    def tearDown(self):
        shutil.rmtree(self.tdir)

    def test_dirs(self):
        shutil.rmtree(self.tdir)
        self.assertFalse(os.path.isdir(self.tdir))

        self.wdir = rain.WorkingDirectory(logger, self.tdir, falseprog)
        self.wdir.clear()
        self.assertTrue(os.path.isdir(self.tdir))

        self.wdir.clear()
        self.assertTrue(os.path.isdir(self.tdir))

        shutil.rmtree(self.tdir)
        with open(self.tdir, 'w') as ofile:
            pass

        self.wdir.clear()

    def test_pushd(self):
        self.wdir.clear()
        
        cwd = os.getcwd()
        absname = os.path.abspath(self.wdir.name)
        with self.wdir.pushd():
            self.assertEqual(os.getcwd(), absname)

        self.assertEqual(os.getcwd(), cwd)

    def test_status(self):
        self.assertEquals(self.wdir.status, None)

        print('self.tdir = {}'.format(self.tdir))

        for i in ['good', 'bad', 'ugly']:
            self.wdir.status = i
            self.assertEquals(self.wdir.status, i)

            # persistence test
            self.wdir = rain.WorkingDirectory(logger, self.tdir, self.ctrlstub)
            self.assertEquals(self.wdir.status, i)


class WorkingDirectorySuccess(WorkingDirectory):
    output = subprocess.DEVNULL
    ctrlstub = trueprog

    def setUp(self):
        WorkingDirectory.setUp(self)

    def test_update(self):
        self.assertTrue(self.wdir.update(self.output))

    def test_build(self):
        self.assertTrue(self.wdir.build(self.output))

    def test_poll(self):
        self.assertTrue(self.wdir.poll(self.output))

    def tearDown(self):
        WorkingDirectory.tearDown(self)

class WorkingDirectoryFailure(WorkingDirectory):
    output = subprocess.DEVNULL
    ctrlstub = falseprog

    def setUp(self):
        WorkingDirectory.setUp(self)

    def test_update(self):
        with self.assertRaises(rain.UpdateError):
            self.wdir.update(self.output)

    def test_build(self):
        with self.assertRaises(rain.BuildError):
            self.wdir.build(self.output)

    def test_poll(self):
        self.assertFalse(self.wdir.poll(self.output))

    def tearDown(self):
        WorkingDirectory.tearDown(self)


@contextlib.contextmanager
def tmpdir(directory='.'):
    temporary_directory = tempfile.mkdtemp(dir=directory)
    yield temporary_directory

    shutil.rmtree(temporary_directory)

# # These need to be rewritten
# class MissingCtrlFile(unittest.TestCase):
#     def test_missingctrlfile(self):
#         with self.assertRaises(rain.MissingCtrlFileError):
#             with tmpdir() as tdir:
#                 wdir = rain.WorkArea(logger, tdir, '/nosuchfilehere')

#     def test_nox(self):
#         with self.assertRaises(rain.NoXCtrlFileError):
#             with tmpdir() as tdir:
#                 wdir = rain.WorkArea(logger, tdir, '/dev/null')

class WorkArea(unittest.TestCase):
    def test_init(self):
        self.assertTrue(rain.WorkArea(logger, 'tests'))

    existing_file_name = 'existing-file'

    def test_file_exists(self):
        with open(self.existing_file_name, 'w') as ofile:
            pass

        with self.assertRaises(rain.WorkAreaAllocationError):
            rain.WorkArea(logger, self.existing_file_name)

        os.remove(self.existing_file_name)

class WorkAreaSuccess(unittest.TestCase):
    def setUp(self):
        self.tdir = tempfile.mkdtemp(dir='tests')
        self.assertTrue(os.path.isdir(self.tdir))
        self.warea = rain.WorkArea(logger, self.tdir, trueprog)
        self.warea.mkstatedir()

    def tearDown(self):
        shutil.rmtree(self.tdir)

    def test_pushd(self):
        startdir = os.getcwd()
        with self.warea.pushd():
            self.assertEquals(os.getcwd(), self.warea.absname)

        self.assertEquals(os.getcwd(), startdir)

    def test_cwd(self):
        self.assertEqual(self.warea.cwd, None)

        self.warea.cwd = 'one'
        self.assertEqual(self.warea.cwd, 'one')

        self.warea.cwd = 'two'
        self.assertEqual(self.warea.cwd, 'two')

        self.warea.cwd = 'three'
        self.assertEqual(self.warea.cwd, 'three')

    def test_wds(self):
        self.assertEquals(self.warea.wds, [''])

        self.warea.wds = self.warea.wds + ['one']
        self.assertEquals(self.warea.wds, ['one'])

        # test persistence by dropping WorkArea and creating another
        # on the same directory.
        self.warea = rain.WorkArea(logger, self.tdir, trueprog)
        self.assertEquals(self.warea.wds, ['one'])

        self.warea.wds = self.warea.wds + ['two']
        self.assertEquals(self.warea.wds, ['one', 'two'])

        self.warea = rain.WorkArea(logger, self.tdir, trueprog)
        self.assertEquals(self.warea.wds, ['one', 'two'])

        self.warea.wds = self.warea.wds + ['three']
        self.assertEquals(self.warea.wds, ['one', 'three', 'two'])

        self.warea = rain.WorkArea(logger, self.tdir, trueprog)
        self.assertEquals(self.warea.wds, ['one', 'three', 'two'])

        self.warea.wds = ['']
        self.assertEquals(self.warea.wds, [''])

    def test_new_wd(self):
        newwd = self.warea.new_working_directory()
        self.assertTrue(os.path.isdir(newwd.absname))


if __name__ == '__main__':
    nose.main()
