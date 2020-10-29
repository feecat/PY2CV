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

import py2cv.globals.constants as c
from PyQt5.QtWidgets import QGraphicsItem
from PyQt5.QtGui import QPen
from PyQt5 import QtCore


class WpZero(QGraphicsItem):
    """
    class WpZero
    """
    def __init__(self, center, color=QtCore.Qt.gray):
        self.sc = None
        super(WpZero, self).__init__()

        self.center = center
        self.allwaysshow = False
        self.color = color
        self.pen = QPen(QtCore.Qt.darkGray, 1, QtCore.Qt.SolidLine)
        self.pen.setCosmetic(True)

        self.diameter = 23.0

    def contains_point(self, point):
        """
        WpZero cannot be selected. Return maximal distance
        """
        return float(0x7fffffff)

    def setSelected(self, *args):
        """
        Override inherited function - with possibility to be called with multiple arguments
        """
        pass

    def paint(self, painter, option, widget=None):
        """
        paint()
        """
        painter.setPen(self.pen)
        demat = painter.deviceTransform()
        self.sc = demat.m11()

        diameter1 = self.diameter / self.sc
        diameter2 = (self.diameter - 4) / self.sc

        rectangle1 = QtCore.QRectF(-diameter1 / 2, -diameter1 / 2, diameter1, diameter1)
        rectangle2 = QtCore.QRectF(-diameter2 / 2, -diameter2 / 2, diameter2, diameter2)
        startAngle1 = 90 * 16
        spanAngle = 90 * 16
        startAngle2 = 270 * 16

        painter.drawEllipse(rectangle1)
        painter.drawEllipse(rectangle2)
        painter.drawPie(rectangle2, startAngle1, spanAngle)

        painter.setBrush(self.color)
        painter.drawPie(rectangle2, startAngle2, spanAngle)

    def boundingRect(self):
        """
        Override inherited function to enlarge selection of Arrow to include all
        @param flag: The flag to enable or disable Selection
        """
        if not self.sc:  # since this function is called before paint; and scale is unknown
            return QtCore.QRectF(0, 0, 1e-9, 1e-9)

        diameter = self.diameter / self.sc
        return QtCore.QRectF(-diameter / 2, -diameter / 2, diameter, diameter)
