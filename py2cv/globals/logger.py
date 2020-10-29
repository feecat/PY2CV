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

from __future__ import absolute_import

import sys
import logging

import py2cv.globals.globals as g


logger = logging.getLogger(__name__)


class LoggerClass(object):
    """
    handle 3 log streams:
        console
        file
        message window
    """
    def __init__(self, root_logger):
        """
        Initialisation of the Logger Class. Only the root logger is initialized
        and the console handler is set. All other handlers needs to be set later
        since the config / window is not present during the start.
        """

        self.root_logger = root_logger

        """
        The level of the root_logger needs to be the highest in order to get
        all messages into the handlers. The handles may have higher logging level
        """
        root_logger.setLevel(logging.DEBUG)

        self.console_handler = logging.StreamHandler(sys.stderr)
        self.console_handler.setLevel(logging.ERROR)

        formatter = logging.Formatter("%(levelname)-10s %(name)-15s %(funcName)-10s %(lineno)-4d:  - %(message)s")
        self.console_handler.setFormatter(formatter)
        root_logger.addHandler(self.console_handler)

    def set_console_handler_loglevel(self):
        """
        This function is used to reset the Loglevel after the config file hase
        been loaded.
        """
        self.console_handler.setLevel(self._cvtlevel(g.config.vars.Logging['console_loglevel']))

    def add_window_logger(self,  stream=sys.stderr):
        """
        Add the logger, which may be used to log to the window. This stream will
        be shown in the messagebox in the canvas window.
        @param stream: The stream which shall be used for writing. Here the
        window will be used. This Class needs a function "def write(self, charstr)
        {DEBUG, INFO, WARNING,  ERROR, CRITICAL}
        """
        self.window_handler = logging.StreamHandler(stream)
        self.window_handler.setLevel(self._cvtlevel(g.config.vars.Logging['window_loglevel']))

        if g.config.vars.Logging['window_loglevel'] == 'INFO':
            self.window_handler.setFormatter(logging.Formatter("%(message)s"))
        else:
            formatter=logging.Formatter("%(levelname)s - %(message)s")
            self.window_handler.setFormatter(formatter)

        self.root_logger.addHandler(self.window_handler)

    def add_file_logger(self):
        """
        Add the logger, which may be used to log to a dedicated file. This logger
        will be enabled all the time.
        """
        self.file_handler = logging.FileHandler(g.config.vars.Logging['logfile'], 'w')  #create
        self.file_handler.setLevel(self._cvtlevel(g.config.vars.Logging['file_loglevel']))
        self.file_handler.setFormatter(logging.Formatter("%(levelname)-10s %(name)-15s %(funcName)-10s %(lineno)-4d:  - %(message)s"))
        self.root_logger.addHandler(self.file_handler)

    def _cvtlevel(self, level):
        """
        This function converts the given logging levels as they are:
        {DEBUG, INFO, WARNING,  ERROR, CRITICAL} to a conform format which is
        required by the function e.g. logging.DEBUG
        @param level: The String with the Level
        @return: Returns the converted string acc. to logging needs.
        """
        if isinstance(level, str):
            return logging.getLevelName(level)
        else:
            return level


class FilterModule(logging.Filter):
    def filter(self, record):
        """A dedicated filter may be added here for debug use
        @param record: The log message is posted here in order to do some checks
        @return: If the value is true it will be shown in the log
        """
        return True
