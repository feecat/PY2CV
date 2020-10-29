# -*- coding: utf-8 -*-

############################################################################
#
#   Copyright (C) 2009-2015
#    Michael Haberler
#
#   This file is part of DXF2GCODE.
#
#   DXF2GCODE is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   DXF2GCODE is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with DXF2GCODE.  If not, see <http://www.gnu.org/licenses/>.
#
############################################################################

"""
Container for global variables accessible to all classes
"""

from __future__ import absolute_import

import os
import sys
import gettext
import locale

import py2cv.globals.constants as constants


# logger instance, see http://docs.python.org/library/logging.html
# once set, use as logger.error("foo")
logger = None

# Config instance
config = None

# Folder of the main instance
folder = None

window = None

quiet = False

#-------------------------------------

# determine Platform
platform = ""
if os.name == "posix" and sys.platform == "darwin":
    platform = "mac"


# Language support
#
langs = []  # list of supported languages

# figure default language
lc, encoding = locale.getdefaultlocale()

if lc:
    langs = [lc]    # if there's one, use as default

language = os.environ.get('LANGUAGE', None)
if language:
    """language comes back something like en_CA:en_US:en_GB:en
    on linuxy systems, on Win32 it's nothing, so we need to
    split it up into a list"""
    langs += language.split(":")

"""Now add on to the back of the list the translations that we
know that we have, our defaults"""
langs += []

"""Now langs is a list of all of the languages that we are going
to try to use.  First we check the default, then what the system
told us, and finally the 'known' list"""

gettext.bindtextdomain(constants.APPNAME,
                       os.path.realpath(os.path.dirname(sys.argv[0])))
gettext.textdomain(constants.APPNAME)
# Get the language to use
trans = gettext.translation(constants.APPNAME, localedir='languages',
                            languages=langs, fallback=True)
trans.install()
