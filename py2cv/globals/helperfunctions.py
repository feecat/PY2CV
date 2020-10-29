# -*- coding: utf-8 -*-

############################################################################
#
#   Copyright (C) 2015-2016
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

from __future__ import absolute_import

import py2cv.globals.constants as c

str_encode = lambda string: string
str_decode = lambda string: string

qstr_encode = lambda string: str_encode(string)

'''
Following two functions are needed for Python3+, since it no longer supports these functions as is
'''
def toInt(text):
    try:
        value = (int(text), True)
    except ValueError:
        value = (0, False)
    return value

def toFloat(text):
    try:
        value = (float(text), True)
    except ValueError:
        value = (0.0, False)
    return value
