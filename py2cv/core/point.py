# -*- coding: utf-8 -*-

############################################################################
#
#   Copyright (C) 2008-2015
#    Christian Kohlöffel
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

import numbers
import logging
logger = logging.getLogger("core.point")

class Point(object):
    __slots__ = ["x", "y"]
    eps=1e-12

    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y

    def __str__(self):
        return 'X ->%6.3f  Y ->%6.3f' % (self.x, self.y)
        # return ('CPoints.append(Point(x=%6.5f, y=%6.5f))' %(self.x,self.y))

    def save_v1(self):
        return 'X -> %6.3f  Y -> %6.3f' % (self.x, self.y)

    def __eq__(self, other):
        """
        Implementaion of is equal of two point, for all other instances it will
        return False
        @param other: The other point for the compare
        @return: True for the same points within tolerance
        """
        if isinstance(other, Point):
            return (-Point.eps < self.x - other.x < Point.eps) and (-Point.eps < self.y - other.y < Point.eps)
        else:
            return False

#     def __cmp__(self, other):
#         """
#         Implementaion of comparing of two point
#         @param other: The other point for the compare
#         @return: 1 if self is bigger, -1 if smaller, 0 if the same
#         """
#         if self.x < other.x:
#             return -1
#         elif self.x > other.x:
#             return 1
#         elif self.x == other.x and self.y < other.y:
#             return -1
#         elif self.x == other.x and self.y > other.y:
#             return 1
#         else:
#             return 0

    def __ne__(self, other):
        """
        Implementation of not equal
        @param other:; The other point
        @return: negative cmp result.
        """
        return not self == other

    def __neg__(self):
        """
        Implemnetaion of Point negation
        @return: Returns a new Point which is negated
        """
        return -1.0 * self

    def __add__(self, other):  # add to another Point
        """
        Implemnetaion of Point addition
        @param other: The other Point which shall be added
        @return: Returns a new Point
        """
        return Point(self.x + other.x, self.y + other.y)

    def __radd__(self, other):
        """
        Implementation of the add for a real value
        @param other: The real value to be added
        @return: Return the new Point
        """
        return Point(self.x + other, self.y + other)

    def __lt__(self,other):
        """
        Implementaion of less then comparision
        @param other: The other point for the compare
        @return: 1 if self is bigger, -1 if smaller, 0 if the same
        """
        if self.x < other.x:
            return True
        elif self.x > other.x:
            return False
        elif self.x == other.x and self.y < other.y:
            return True
        elif self.x == other.x and self.y > other.y:
            return False
        else:
            return 0

    def __sub__(self, other):
        """
        Implemnetaion of Point subtraction
        @param other: The other Point which shall be subtracted
        @return: Returns a new Point
        """
        return self + -other

    def __rmul__(self, other):
        """
        Multiplication by a real value
        @param other: The real value to be multiplied by
        @return: The new poinnt
        """

        return Point(other * self.x, other * self.y)

    def __mul__(self, other):
        """
        The function which is called if the object is multiplied with another
        object. Dependent on the object type different operations are performed
        @param other: The element which is used for the multiplication
        @return: Returns the result dependent on object type
        """
        if isinstance(other, list):
            # Scale the points
            return Point(x=self.x * other[0], y=self.y * other[1])
        elif isinstance(other, numbers.Number):
            return Point(x=self.x * other, y=self.y * other)
        elif isinstance(other, Point):
            # Calculate Scalar (dot) Product
            return self.x * other.x + self.y * other.y
        else:
            logger.warning("Unsupported type: %s" % type(other))

    def __truediv__(self, other):
        return Point(x=self.x / other, y=self.y / other)

    def tr(self, message):
        return message

    def between(self, B, C):
        """
        is c between a and b?     // Reference: O' Rourke p. 32
        @param B: a second point
        @param C: a third point
        @return: If C is between those points
        """
        if self.ccw(B, C) != 0:
            return False
        if (self.x == B.x) and (self.y == B.y):
            return (self.x == C.x) and (self.y == C.y)

        elif self.x != B.x:
            # ab not vertical
            return ((self.x <= C.x) and (C.x <= B.x)) or ((self.x >= C.x) and (C.x >= B.x))

        else:
            # ab not horizontal
            return ((self.y <= C.y) and (C.y <= B.y)) or ((self.y >= C.y) and (C.y >= B.y))

    def ccw(self, B, C):
        """
        This functions gives the Direction in which the three points are located.
        @param B: a second point
        @param C: a third point
        @return: If the slope of the line AB is less than the slope of the line
        AC then the three points are listed in a counterclockwise order
        """
        # return (C.y-self.y)*(B.x-self.x) > (B.y-self.y)*(C.x-self.x)

        area2 = (B.x - self.x) * (C.y - self.y) - (C.x - self.x) * (B.y - self.y)
        # logger.debug(area2)
        if area2 < -Point.eps:
            return -1
        elif area2 > Point.eps:
            return +1
        else:
            return 0

    def cross_product(self, other):
        """
        Returns the cross Product of two points
        @param P1: The first Point
        @param P2: The 2nd Point
        @return: dot Product of the points.
        """
        return Point(self.y * other.z - self.z * other.y,
                     self.z * other.x - self.x * other.z,
                     self.x * other.y - self.y * other.x)

    def distance(self, other=None):
        """
        Returns distance between two given points
        @param other: the other geometry
        @return: the minimum distance between the the given geometries.
        """
        if other is None:
            other = Point(x=0.0, y=0.0)
        if not isinstance(other, Point):
            return other.distance(self)
        return (self - other).length()

#     def distance2_to_line(self, Ps, Pe):
#         dLine = Pe - Ps
#
#         u = ((self.x - Ps.x) * dLine.x + (self.y - Ps.y) * dLine.y) / dLine.length_squared()
#         if u > 1.0:
#             u = 1.0
#         elif u < 0.0:
#             u = 0.0
#
#         closest = Ps + u * dLine
#         diff = closest - self
#         return diff.length_squared()

    def dotProd(self, P2):
        """
        Returns the dotProduct of two points
        @param self: The first Point
        @param other: The 2nd Point
        @return: dot Product of the points.
        """
        return (self.x * P2.x) + (self.y * P2.y)

    def get_arc_point(self, ang=0, r=1):
        """
        Returns the Point on the arc defined by r and the given angle, self is
        Center of the arc
        @param ang: The angle of the Point
        @param radius: The radius from the given Point
        @return: A Point at given radius and angle from Point self
        """
        return Point(x=self.x + cos(ang) * r, \
                     y=self.y + sin(ang) * r)

    def get_normal_vector(self, other, r=1):
        """
        This function return the Normal to a vector defined by self and other
        @param: The second point
        @param r: The length of the normal (-length for other direction)
        @return: Returns the Normal Vector
        """
        unit_vector = self.unit_vector(other)
        return Point(x=unit_vector.y * r, y=-unit_vector.x * r)

    def get_nearest_point(self, points):
        """
        If there are more then 1 intersection points then use the nearest one to
        be the intersection Point.
        @param points: A list of points to be checked for nearest
        @return: Returns the nearest Point
        """
        if len(points) == 1:
            Point = points[0]
        else:
            mindis = points[0].distance(self)
            Point = points[0]
            for i in range(1, len(points)):
                curdis = points[i].distance(self)
                if curdis < mindis:
                    mindis = curdis
                    Point = points[i]

        return Point

    def length(self):
        return sqrt(self.length_squared())

    def length_squared(self):
        return self.x**2 + self.y**2

    def norm_angle(self, other=None):
        """Returns angle between two given points"""
        if type(other) == type(None):
            other = Point(x=0.0, y=0.0)
        return atan2(other.y - self.y, other.x - self.x)

    def rot_sca_abs(self, sca=None, p0=None, pb=None, rot=None, parent=None):
        """
        Generates the absolute geometry based on the geometry self and the
        parent. If reverse = 1 is given the geometry may be reversed.
        @param sca: The Scale
        @param p0: The Offset
        @param pb: The Base Point
        @param rot: The angle by which the contour is rotated around p0
        @param parent: The parent of the geometry (EntityContentClass)
        @return: A new Point which is absolute position
        """
        if sca is None and parent is not None:
            p0 = parent.p0
            pb = parent.pb
            sca = parent.sca
            rot = parent.rot

            pc = self - pb
            cos_rot = cos(rot)
            sin_rot = sin(rot)
            rotx = (pc.x * cos_rot + pc.y * -sin_rot) * sca[0]
            roty = (pc.x * sin_rot + pc.y * cos_rot) * sca[1]
            p1 = Point(rotx, roty) + p0

            # Recursive loop if the point self is  introduced
            if parent.parent is not None:
                p1 = p1.rot_sca_abs(parent=parent.parent)

        elif parent is None and sca is None:
            # no rotation/scaling
            p1 = self

        else:
            pc = self - pb
            cos_rot = cos(rot)
            sin_rot = sin(rot)
            rotx = (pc.x * cos_rot + pc.y * -sin_rot) * sca[0]
            roty = (pc.x * sin_rot + pc.y * cos_rot) * sca[1]
            p1 = Point(rotx, roty) + p0

#        print(("Self:    %s\n" % self)+\
#              ("P0:      %s\n" % p0)+\
#              ("Pb:      %s\n" % pb)+\
#              ("Pc:      %s\n" % pc)+\
#              ("rot:     %0.1f\n" % degrees(rot))+\
#              ("sca:     %s\n" % sca)+\
#              ("P1:      %s\n\n" % p1))

        return p1

    def to3D(self, z=0.0):
        pass

    def transform_to_Norm_Coord(self, other, alpha):
        xt = other.x + self.x * cos(alpha) + self.y * sin(alpha)
        yt = other.y + self.x * sin(alpha) + self.y * cos(alpha)
        return Point(x=xt, y=yt)

    def triangle_height(self, other1, other2):
        """
        Calculate height of triangle given lengths of the sides
        @param other1: Point 1 for triangle
        @param other2: Point 2 for triangel
        """
        # The 3 lengths of the triangle to calculate
        a = self.distance(other1)
        b = other1.distance(other2)
        c = self.distance(other2)
        return sqrt(pow(b, 2) - pow((pow(c, 2) + pow(b, 2) - pow(a, 2)) / (2 * c), 2))

    def trim(self, Point, dir=1, rev_norm=False):
        """
        This instance is used to trim the geometry at the given point. The point
        can be a point on the offset geometry a perpendicular point on line will
        be used for trimming.
        @param Point: The point / perpendicular point for new Geometry
        @param dir: The direction in which the geometry will be kept (1  means the
        being will be trimmed)
        """
        if not(hasattr(self, "end_normal")):
            return self
        new_normal = self.unit_vector(Point)
        if rev_norm:
            new_normal = -new_normal
        if dir == 1:
            self.start_normal = new_normal
            return self
        else:
            self.end_normal = new_normal
            return self

    def unit_vector(self, Pto=None, r=1):
        """
        Returns vector of length 1 with similar direction as input
        @param Pto: The other point
        @return: Returns the Unit vector
        """
        if Pto is None:
            return self / self.length()
        else:
            diffVec = Pto - self
            l = diffVec.distance()
            return Point(diffVec.x / l * r, diffVec.y / l * r)

    def within_tol(self, other, tol):
        """
        Are the two points within tolerance
        """
        # TODO is this sufficient, or do we want to compare the distance
        return abs(self.x - other.x) <= tol and abs(self.y - other.y) < tol

    def plot2plot(self, plot, format='xr'):
        plot.plot([self.x], [self.y], format)
