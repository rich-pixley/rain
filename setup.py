#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Time-stamp: <23-Dec-2013 14:17:45 PST by rich@noir.com>

# Copyright © 2013 K Richard Pixley, All Rights Reserved.

import os
import platform

import distribute_setup
distribute_setup.use_setuptools()

import setuptools

__docformat__ = "restructuredtext en"

me='K Richard Pixley'
memail='rich@noir.com'

install_requires = [
]

setup_requirements = install_requires + [
    'nose',
    'setuptools_git',
]

version_tuple = platform.python_version_tuple()
version = platform.python_version()

if version not in [
    '3.0.1',
    '3.1.5',
    '3.3.1',
    ]:
    setup_requirements.append('setuptools_lint')

if version not in [
    '3.0.1',
    ]:
    setup_requirements.append('sphinx>=1.0.5')


setuptools.setup(
    name='rain',
    version='0.0',
    author=me,
    maintainer=me,
    author_email=memail,
    maintainer_email=memail,
    keywords='',
    url = 'https://github.com/rich-pixley/rain',
    download_url = 'https://api.github.com/repos/rich-pixley/rain/tarball',
    description='A flexible and extendable automated builder.',
    license='GPL2',
    long_description='',
    setup_requires=setup_requirements,
    install_requires=install_requires,
    py_modules=['rain'],
    packages=setuptools.find_packages(),
    include_package_data=True,
    test_suite='nose.collector',
    scripts = [],
    provides=[
        'rain',
        ],
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Software Development :: Testing',
        'Topic :: Utilities',
        ],
    entry_points = {
        'console_scripts': [
            'rain = rain.main:main',
        ],
        # 'gui_scripts': [
        #     'baz = my_package_gui.start_func',
        # ]
    },
)
