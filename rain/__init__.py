#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Time-stamp: <18-Feb-2014 16:08:40 PST by rich@mito>

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


class WorkAreaAllocationError(RainException):
    """Raised when we can't mkdir a WorkArea"""
    pass

class AllocationError(RainException):
    """Raised when we can't allocate a workspace."""
    pass


