#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Time-stamp: <23-Dec-2013 14:21:43 PST by rich@noir.com>

# Copyright © 2013 K Richard Pixley

'''
Class representing disk locations.
'''

class DiskLocation:
    locationName = None

    def __init__(self, locationName=None):
        self.locationName = locationName
