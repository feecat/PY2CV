# -*- coding: utf-8 -*-

############################################################################
#
#   Copyright (C) 2008-2015
#    Christian Kohl�ffel
#    Vinzenz Schulz
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
from __future__ import division

from math import sqrt, sin, cos, atan2
from copy import deepcopy

from py2cv.core.point import Point

import logging
logger = logging.getLogger("core.boundingbox")

eps=-1e-12

class BoundingBox:
    """ 
    Bounding Box Class. This is the standard class which provides all std. 
    Bounding Box methods.
    """
    def __init__(self, Ps=Point(0, 0), Pe=Point(0, 0), hdl=[]):
        """ 
        Standard method to initialize the class
        """

        self.Ps = Ps
        self.Pe = Pe


    def __str__(self):
        """ 
        Standard method to print the object
        @return: A string
        """
        s = ("\nPs : %s" % (self.Ps)) + \
           ("\nPe : %s" % (self.Pe))
        return s

    def joinBB(self, other):
        """
        Joins two Bounding Box Classes and returns the new one
        @param other: The 2nd Bounding Box
        @return: Returns the joined Bounding Box Class
        """

        if type(self.Ps) == type(None) or type(self.Pe) == type(None):
            return BoundingBox(deepcopy(other.Ps), deepcopy(other.Pe))

        xmin = min(self.Ps.x, other.Ps.x)
        xmax = max(self.Pe.x, other.Pe.x)
        ymin = min(self.Ps.y, other.Ps.y)
        ymax = max(self.Pe.y, other.Pe.y)

        return BoundingBox(Ps=Point(xmin, ymin), Pe=Point(xmax, ymax))

    def hasintersection(self, other=None, tol=eps):
        """
        Checks if the two bounding boxes have an intersection
        @param other: The 2nd Bounding Box
        @return: Returns true or false
        """
        if isinstance(other, Point):
            return self.pointisinBB(other, tol)
        elif isinstance(other, BoundingBox):
            x_inter_pos = (self.Pe.x + tol > other.Ps.x) and \
            (self.Ps.x - tol < other.Pe.x)
            y_inter_pos = (self.Pe.y + tol > other.Ps.y) and \
            (self.Ps.y - tol < other.Pe.y)

            return x_inter_pos and y_inter_pos
        else:
            logger.warning("Unsupported Instance: %s" % other.type)

    def iscontained(self, other):
        """
        Checks if self Bounding Box is contained in Boundingbox of other
        @param other: The 2nd Bounding Box
        @return: Returns true or false
        """
        return  other.Ps.x < self.Ps.x and self.Pe.x < other.Pe.x and\
            other.Ps.y < self.Ps.y and self.Pe.y < other.Pe.y


    def pointisinBB(self, Point=Point(), tol=eps):
        """
        Checks if the Point is within the bounding box
        @param Point: The Point which shall be ckecke
        @return: Returns true or false
        """
        x_inter_pos = (self.Pe.x + tol > Point.x) and \
        (self.Ps.x - tol < Point.x)
        y_inter_pos = (self.Pe.y + tol > Point.y) and \
        (self.Ps.y - tol < Point.y)
        return x_inter_pos and y_inter_pos
