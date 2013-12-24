#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Time-stamp: <23-Dec-2013 16:14:41 PST by rich@noir.com>

# Copyright © 2013 K Richard Pixley

"""
Shell callable driver for the :py:mod:`rain`.
"""

import argparse
import fnmatch
import logging
import os
import re
import contextlib
import subprocess
import shlex

import rain

__docformat__ = "restructuredtext en"

@contextlib.contextmanager
def pushdir(newdir):
    savedir = os.getcwd()
    os.chdir(newdir)
    yield

    os.chdir(savedir)

class EmacsBuild:
    @staticmethod
    def build(workspace):
        try:
            with pushdir(workspace.name):
                subprocess.check_call(shlex.split('tar xfJ /home/rich/local/src/emacs-24.3.tar.xz'))
                with pushdir('emacs-24.3'):
                    subprocess.check_call(shlex.split('./configure --with-x-toolkit=no --with-xpm=no --with-jpeg=no --with-png=no --with-gif=no --with-tiff=no'))
                    subprocess.check_call(shlex.split('time make -j4'))

        except:
            return False

        return True

def main():
    location = Location('.')
    workspace = location.next_workspace()
    
if __name__ == '__main__':
    main()
