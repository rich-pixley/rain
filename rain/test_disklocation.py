#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Time-stamp: <23-Dec-2013 14:31:17 PST by rich@noir.com>

# Copyright © 2013 K Richard Pixley

'''
tests.
'''

import nose

import rain.disklocation

class testBasics:
    def testDefault(self):
        nose.tools.assert_equal(None, rain.disklocation.DiskLocation().locationName)

    def testSimple(self):
        name = 'simple'
        nose.tools.assert_equal(name, rain.disklocation.DiskLocation(name).locationName)
        
    def testNamed(self):
        name = 'named'
        nose.tools.assert_equal(name, rain.disklocation.DiskLocation(locationName=name).locationName)
