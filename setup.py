# -*- coding: utf-8 -*-

#*****************************************************************************
#       Copyright (C) 2003-2006 Gary Bishop.
#       Copyright (C) 2006  Jorgen Stenarson. <jorgen.stenarson@bostream.nu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

import os
import sys

from setuptools import setup, find_packages
from setuptools.command.test import test

# BEFORE importing distutils, remove MANIFEST. distutils doesn't properly
# update it when the contents of directories change.
if os.path.exists('MANIFEST'):
    os.remove('MANIFEST')

exec(open('pyreadline/release.py', 'Ur').read())

setup(
    name=name,
    version= version,
    description= description,
    long_description= long_description,
    author= authors["Jorgen"][0],
    author_email= authors["Jorgen"][1],
    maintainer= authors["Jorgen"][0],
    maintainer_email = authors["Jorgen"][1],
    license          = license,
    classifiers      = classifiers,
    url              = url,
    platforms        = platforms,
    keywords         = keywords,
    py_modules       = ['readline'],
    packages         = ['pyreadline'],
    tests_require=['unittest2'],
    test_suite='unittest2.collector'
)
