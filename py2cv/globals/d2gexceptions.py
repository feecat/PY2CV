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
user defined exceptions
"""


class BadConfigFileError(SyntaxError):
    """
    syntax error in config file
    """
    def __init__(self, value):
        print("bin hier")
        self.value = value

    def __str__(self):
        return repr(self.value)


class VersionMismatchError(Exception):
    """
    version mismatch in config file
    """
    def __init__(self, fileversion, CONFIG_VERSION):
        self.fileversion = fileversion
        self.CONFIG_VERSION = CONFIG_VERSION

    def __str__(self):
        return repr('config file versions do not match - internal: %s,'
                    ' config file: %s - delete existing file to resolve issue'
                    % (self.CONFIG_VERSION, self.fileversion))


class OptionError(SyntaxError):
    """
    conflicting command line option
    """


class PluginError(SyntaxError):
    """
    something went wrong during plugin loading or initialization
    """
