#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Time-stamp: <19-Feb-2014 16:31:35 PST by rich@noir.com>

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


