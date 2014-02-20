#!/usr/bin/make -f
# -*- coding: utf-8 -*-
#
# Time-stamp: <20-Feb-2014 13:55:25 PST by rich@noir.com>

# Copyright © 2014 K Richard Pixley

# update should make the working directory source current as of the
# top of tree repository.

update: make/configure
	(cd make && git pull)

make/configure:; git clone ~/projects/make

# build brings the working directory binaries up to date

build:;	(cd make && ./configure && make -j6)

# poll should succeed if there is something new to build and fail
# otherwise.
poll:; (cd make && git fetch && git st | grep behind > /dev/null)
