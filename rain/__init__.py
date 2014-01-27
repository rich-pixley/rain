#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Time-stamp: <26-Jan-2014 18:41:54 PST by rich@noir.com>

# Copyright © 2013 K Richard Pixley

"""
Class representing disk locations.

.todo: workspace as context manager?
"""

__docformat__ = 'restructuredtext en'

__all__ = [
]

import os
import shutil
import logging

logger = logging.getLogger(__name__)

class RainException(Exception):
    """Base class for all :py:mod:`rain` exceptions"""
    pass


class WorkSpace:
    """Very simple workspace object."""

    name = None
    logger = None

    def __init__(self, name=None, logger=logger):
        self.name = name
        self.logger = logger

    def create(self):
        """called to create the work space"""
        self.logger.log(logging.DEBUG, 'os.mkdir %s', self.name)
        os.mkdir(self.name)

    def remove(self):
        self.logger.log(logging.DEBUG, 'shutil.rmtree %s', self.name)
        shutil.rmtree(self.name)


class AllocationError(RainException):
    """Raised when we can't allocate a workspace."""
    pass


class Location:
    '''
    Brain dead allocator.  Assume local disk, single work space.
    '''

    name = None
    workspace = None

    def __init__(self, name='.', logger=logger):
        self.name = name
        self.workspace = None

    def next_workspace(self):
        if self.workspace:
            raise AllocationError

        self.workspace = WorkSpace(os.path.join(self.name, 'WorkSpace'))
        self.workspace.create()
        return self.workspace

    def remove_workspace(self, workspace):
        if workspace is not self.workspace:
            raise AllocationError

        self.workspace.remove()
        self.workspace = None

