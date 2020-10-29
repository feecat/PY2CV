# -*- coding: utf-8 -*-

############################################################################
#
#   Copyright (C) 2010-2015
#    Christian Kohlöffel
#    Jean-Paul Schouwstra
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
All global constants are initialized in this module.
They are used in the other modules.

see http://code.activestate.com/recipes/65207/ for module const

@purpose:  initialization of the global constants used within the other modules.
"""

import logging

import platform

from PyQt5 import QtCore

# Global Variables
APPNAME = "PY2CV"
VERSION = "Py%s PyQt%s" % (platform.python_version(), QtCore.PYQT_VERSION_STR)

DATE     =  "$Date: Fri Sep 25 16:00:00 2020 +0800 $"
REVISION =  "$Revision: cd19f2420da8d0845363d0fb120edc130ddf50a5 $"
AUTHOR   = u"$Author: Damian Wrobel <dwrobel@ertelnet.rybnik.pl>, Last Modify: feecat $"

CONFIG_EXTENSION = '.cfg'
PY_EXTENSION = '.py'
PROJECT_EXTENSION = '.p2c'

# Rename unreadable config/varspace files to .bad
BAD_CONFIG_EXTENSION = '.bak'
DEFAULT_CONFIG_DIR = 'config'
DEFAULT_POSTPRO_DIR = 'postpro_config'

# log related
DEFAULT_LOGFILE = 'py2cv.log'
STARTUP_LOGLEVEL = logging.DEBUG
# PRT = logging.INFO
