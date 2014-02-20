#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Time-stamp: <20-Feb-2014 13:03:21 PST by rich@noir.com>

# Copyright © 2013 - 2014 K Richard Pixley

"""
Shell callable driver for :py:mod:`rain`.

fixme: need incremental builds before we can poll

fixme: need a mechanism for working directory name normalization for
builds that bolt full path names.

"""

import argparse
import logging
import shutil

import rain

__docformat__ = "restructuredtext en"

REMOVAL_CMDS = ['remove', 'rm', 'delete', 'del']

def main():
    """main"""
    logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%Y-%m-%dT%H:%M:%S%z')
    logger = logging.getLogger()

    options = _parse_args()

    log_level = logging.INFO

    if options.verbose > 0:
        log_level = logging.DEBUG

    logger.setLevel(log_level)

    area = rain.WorkArea(logger)

    retval = False # True on error

    if options.action in ['build']:
        counter = options.count
        while options.count == 0 or counter > 0:
            retval |= area.do_pass(options.keep)
            counter -= 1

    elif options.action in ['ls']:
        stuff = '\n'.join(area.raindirs())
        if stuff:
            print(stuff)

    elif options.action in ['keep']:
        area.keep(options.count)

    # elif options.action in ['poll']:
    #     return area.poll(logfile)

    elif options.action in REMOVAL_CMDS:
        for directory in area.raindirs()[:options.count]:
            shutil.rmtree(directory)

    return retval


def _parse_args():
    """
    Parses the command line arguments.

    :return: Namespace with arguments.
    :rtype: Namespace
    """
    parser = argparse.ArgumentParser(description='rain - a new sort of automated builder.')

    parser.add_argument('action', help='what shall we do?', default='build', nargs='?',
                        choices=['build',
                                 'ls',
                                 'keep',
                                 'poll'] + REMOVAL_CMDS)

    parser.add_argument('-c', '--count', type=int, default=1,
                        help='a count of items on which to operate. [default: %(default)s]')

    parser.add_argument('--keep', type=int, default=-1,
                        help='how many builds should we keep around? [default: %(default)s]')

    parser.add_argument('-v', '--verbose', action='count', default=0, help='Be more verbose. (can be repeated)')

    parser.add_argument('--version', default=False, action='store_true',
                        help='print version number and exit. [default: %(default)s]')

    return parser.parse_args()

if __name__ == '__main__':
    main()
