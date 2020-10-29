# -*- coding: utf-8 -*-# -*- coding: utf-8 -*-

############################################################################
#
#   Copyright (C) 2014-2015
#    Robert Lichtenberger
#    Wojciech Nycz
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

from copy import deepcopy

from py2cv.core.linegeo import LineGeo


class BreakGeo(LineGeo):
    """
    BreakGeo interrupts another geometry item by changing the Z-Position.
    """
    def __init__(self, Ps, Pe, height, xyfeed, zfeed):
        LineGeo.__init__(self, Ps, Pe)

        self.height = height
        self.xyfeed = xyfeed
        self.zfeed = zfeed

    def __deepcopy__(self, memo):
        return BreakGeo(deepcopy(self.Ps, memo),
                        deepcopy(self.Pe, memo),
                        deepcopy(self.height, memo),
                        deepcopy(self.xyfeed, memo),
                        deepcopy(self.zfeed, memo))

    def __str__(self):
        """
        Standard method to print the object
        @return: A string
        """
        return "\nBreakGeo" +\
               "\nPs:     %s" % self.Ps +\
               "\nPe:     %s" % self.Pe +\
               "\nheight: %0.5f" % self.height

    def save_v1(self):
        """
        Standard method to print the object
        @return: A string
        """
        return "\nBreakGeo" +\
               "\nPs:     %s" % self.Ps.save_v1() +\
               "\nPe:     %s" % self.Pe.save_v1() +\
               "\nheight: %0.5f" % self.height

    def Write_GCode(self, PostPro):
        """
        Writes the GCODE for a Break.
        @param PostPro: The PostProcessor instance to be used
        @return: Returns the string to be written to file.
        """
        oldZ = PostPro.ze
        oldFeed = PostPro.feed
        if self.height <= oldZ:
            return (
                LineGeo.Write_GCode(self, PostPro)
            )
        else:
            return (
                PostPro.chg_feed_rate(self.zfeed) +
                PostPro.lin_pol_z(self.height) +
                PostPro.chg_feed_rate(self.xyfeed) +
                LineGeo.Write_GCode(self, PostPro) +
                PostPro.chg_feed_rate(self.zfeed) +
                PostPro.lin_pol_z(oldZ) +
                PostPro.chg_feed_rate(oldFeed)
            )
