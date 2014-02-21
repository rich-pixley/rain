#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Time-stamp: <20-Feb-2014 16:29:31 PST by rich@noir.com>

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

class MissingMk(unittest.TestCase):
    def test_missingmkfile(self):
        with self.assertRaises(rain.MissingMkfileError):
            tdir = tempfile.mkdtemp()
            wdir = rain.WorkingDirectory(logger, tdir)
            os.rmdir(tdir)

class WorkingDirectory(unittest.TestCase):
    def setUp(self):
        self.tdir = tempfile.mkdtemp(dir='tests')
        self.assertTrue(os.path.isdir(self.tdir))

        self.wdir = rain.WorkingDirectory(logger, self.tdir)
        self.wdir.clear()

    def test_dirs(self):
        shutil.rmtree(self.tdir)
        self.assertFalse(os.path.isdir(self.tdir))

        self.wdir = rain.WorkingDirectory(logger, self.tdir)
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
        with self.wdir.pushd():
            for i in ['good', 'bad', 'ugly']:
                self.wdir.status(i)

                with open(self.wdir.statusfilename, 'r') as ifile:
                    self.assertEquals(ifile.read().strip(), i)

            os.remove(self.wdir.statusfilename)

    def tearDown(self):
        shutil.rmtree(self.tdir)


class WorkingDirectorySuccess(WorkingDirectory):
    successmkname = os.path.join(os.path.abspath('tests'), 'rain-stub-success.mk')
    output = subprocess.DEVNULL

    def setUp(self):
        WorkingDirectory.setUp(self)
        self.successmk = os.path.join(self.wdir.absname, 'rain.mk')
        logger.info('ln {} {}'.format(self.successmkname, self.successmk))
        os.link(self.successmkname, self.successmk)

    def test_update(self):
        self.assertTrue(self.wdir.update(self.output))

    def test_build(self):
        self.assertTrue(self.wdir.build(self.output))

    def test_poll(self):
        self.assertTrue(self.wdir.poll(self.output))

    def tearDown(self):
        WorkingDirectory.tearDown(self)

class WorkingDirectoryFailure(WorkingDirectory):
    successmkname = os.path.join(os.path.abspath('tests'), 'rain-stub-failure.mk')
    output = subprocess.DEVNULL

    def setUp(self):
        WorkingDirectory.setUp(self)
        self.successmk = os.path.join(self.wdir.absname, 'rain.mk')
        logger.info('ln {} {}'.format(self.successmkname, self.successmk))
        os.link(self.successmkname, self.successmk)

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

if __name__ == '__main__':
    nose.main()
