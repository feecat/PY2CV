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


class EntityContent(object):
    def __init__(self, nr, name, parent, p0, pb, sca, rot):
        """
        @param p0: The Starting Point to plot (Default x=0 and y=0)
        @param bp: The Base Point to insert the geometry and base for rotation
        (Default is also x=0 and y=0)
        @param sca: The scale of the basis function (default =1)
        @param rot: The rotation of the geometries around base (default =0)
        """
        self.nr = nr
        self.name = name
        self.parent = parent
        self.children = []
        self.p0 = p0
        self.pb = pb
        self.sca = sca
        self.rot = rot

    def __str__(self):
        return "\nEntityContent" +\
               "\nnr :      %i" % self.nr +\
               "\nname:     %s" % self.name +\
               "\nchildren: %s" % self.children +\
               "\np0:       %s" % self.p0 +\
               "\npb:       %s" % self.pb +\
               "\nsca:      %s" % self.sca +\
               "\nrot:      %s" % self.rot

    def append(self, child):
        self.children.append(child)
