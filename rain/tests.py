#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Time-stamp: <23-Dec-2013 15:15:38 PST by rich@noir.com>

# Copyright © 2013 K Richard Pixley

'''
tests.
'''

import nose

import rain

verbose_logging = False
if verbose_logging:
    import logging
    logger = logging.getLogger()
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    logger.addHandler(handler)

class testLocation:
    def testDefault(self):
        nose.tools.assert_equal('.', rain.Location().name)

    def testSimple(self):
        name = 'simple'
        nose.tools.assert_equal(name, rain.Location(name).name)
        
    def testNamed(self):
        name = 'named'
        nose.tools.assert_equal(name, rain.Location(name=name).name)
