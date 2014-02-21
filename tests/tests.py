#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Time-stamp: <20-Feb-2014 19:38:22 PST by rich@noir.com>

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


class isodate(unittest.TestCase):

    def test_isodate(self):
        self.assertEqual(len(rain.isodate()), 26)

class WorkingDirectory(unittest.TestCase):
    mkstub = '/bin/true'

    def setUp(self):
        self.tdir = tempfile.mkdtemp(dir='tests')
        self.assertTrue(os.path.isdir(self.tdir))

        self.wdir = rain.WorkingDirectory(logger, self.tdir, self.mkstub)
        self.wdir.clear()

    def test_dirs(self):
        shutil.rmtree(self.tdir)
        self.assertFalse(os.path.isdir(self.tdir))

        self.wdir = rain.WorkingDirectory(logger, self.tdir, '/bin/false')
        self.wdir.clear()
        self.assertTrue(os.path.isdir(self.tdir))

        self.wdir.clear()
        self.assertTrue(os.path.isdir(self.tdir))

        os.rmdir(self.tdir)
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
        print('test_status')
        print(self.wdir.status)
        self.assertEquals(self.wdir.status, None)

        for i in ['good', 'bad', 'ugly']:
            self.wdir.status = i
            self.assertEquals(self.wdir.status, i)

    def tearDown(self):
        shutil.rmtree(self.tdir)


class WorkingDirectorySuccess(WorkingDirectory):
    output = subprocess.DEVNULL

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
    mkstub = '/bin/false'

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
        self.warea = rain.WorkArea(logger, self.tdir, '/bin/true')

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

        del self.warea.cwd
        self.assertRaises(AttributeError, lambda: self.warea.cwd)

    def test_wds(self):
        self.assertEquals(self.warea.wds, [''])

        self.warea.wds = self.warea.wds + ['one']
        self.assertEquals(self.warea.wds, ['one'])

        self.warea.wds = self.warea.wds + ['two']
        self.assertEquals(self.warea.wds, ['one', 'two'])

        self.warea.wds = self.warea.wds + ['three']
        self.assertEquals(self.warea.wds, ['one', 'three', 'two'])

        self.warea.wds = ['']
        self.assertEquals(self.warea.wds, [''])

    def test_new_wd(self):
        newwd = self.warea.new_working_directory()
        self.assertTrue(os.path.isdir(newwd.absname))


if __name__ == '__main__':
    nose.main()
