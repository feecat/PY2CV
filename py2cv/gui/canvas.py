# -*- coding: utf-8 -*-

############################################################################
#
#   Copyright (C) 2011-2015
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

from __future__ import absolute_import

import logging

import py2cv.globals.globals as g

import py2cv.globals.constants as c
from PyQt5.QtWidgets import QGraphicsView, QMenu
from PyQt5 import QtCore
from PyQt5.QtGui import QMouseEvent, QKeyEvent
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt


logger = logging.getLogger("DxfImport.myCanvasClass")

"""
This Canvas function can be called as any class.
Since it will pretend to be, depending on the settings,
to be the canvas3d or canvas2d class
"""
def Canvas(parent=None):
    from py2cv.gui.canvas2d import MyGraphicsView
    return MyGraphicsView(parent)

def CanvasObject():
    return QGraphicsView

class CanvasBase(CanvasObject()):
    def __init__(self, parent=None):
        super(CanvasBase, self).__init__(parent)

        self.isPanning = False
        self.isRotating = False
        self.isMultiSelect = False

        self.setMouseTracking (True)


    def updateModifiers(self, event):
        """
        Handle all canvas keyboard modifiers in one place.
        """

        if type (event) == QMouseEvent:
            buttons = event.buttons()
        else:
            buttons = QApplication.mouseButtons()

        if type (event) == QKeyEvent:
            modifiers = event.modifiers()
        else:
            modifiers = QApplication.keyboardModifiers()

        # allow only clean modifiers, no combos
        wantMultiSelect = (modifiers == Qt.ControlModifier)
        self.isMultiSelect = wantMultiSelect and ((buttons == Qt.NoButton) or (buttons == Qt.LeftButton))
        wantPanning = (modifiers == Qt.ShiftModifier)
        self.isPanning = wantPanning and (buttons == Qt.LeftButton)
        wantRotating = (modifiers == Qt.AltModifier)
        self.isRotating = wantRotating and (buttons == Qt.LeftButton)

        if self.isPanning or self.isRotating:
            self.setCursor(Qt.ClosedHandCursor)
        elif wantPanning:
            self.setCursor(Qt.OpenHandCursor)
        elif wantRotating:
            self.setCursor(Qt.PointingHandCursor)
        elif wantMultiSelect:
            self.setCursor(Qt.CrossCursor)
        else:
            self.unsetCursor()


class MyDropDownMenu(QMenu):
    def __init__(self, canvas_scene, position, clicked, offset=None):
        QMenu.__init__(self)

        self.clicked = clicked
        self.offset = offset

        self.canvas_scene = canvas_scene

        #self.selectedItems = [shape for shape in canvas_scene.shapes if shape.isSelected()]
        
        self.selectedItems = []

        if len(self.selectedItems) == 0:
            return

        invertAction = self.addAction(self.tr("Invert Selection"))
        disableAction = self.addAction(self.tr("Disable Selection"))
        enableAction = self.addAction(self.tr("Enable Selection"))

        self.addSeparator()

        swdirectionAction = self.addAction(self.tr("Switch Direction"))
        SetNxtStPAction = self.addAction(self.tr("Set Nearest StartPoint"))

        if g.config.machine_type == 'drag_knife':
            pass
        else:
            self.addSeparator()
            submenu1 = QMenu(self.tr('Cutter Compensation'), self)
            self.noCompAction = submenu1.addAction(self.tr("G40 No Compensation"))
            self.noCompAction.setCheckable(True)
            self.leCompAction = submenu1.addAction(self.tr("G41 Left Compensation"))
            self.leCompAction.setCheckable(True)
            self.reCompAction = submenu1.addAction(self.tr("G42 Right Compensation"))
            self.reCompAction.setCheckable(True)

            logger.debug(self.tr("The selected shapes have the following direction: %i") % (self.calcMenuDir()))
            self.checkMenuDir(self.calcMenuDir())

            self.addMenu(submenu1)

        invertAction.triggered.connect(self.invertSelection)
        disableAction.triggered.connect(self.disableSelection)
        enableAction.triggered.connect(self.enableSelection)

        swdirectionAction.triggered.connect(self.switchDirection)
        SetNxtStPAction.triggered.connect(self.setNearestStPoint)

        if g.config.machine_type == 'drag_knife':
            pass
        else:
            self.noCompAction.triggered.connect(self.setNoComp)
            self.leCompAction.triggered.connect(self.setLeftComp)
            self.reCompAction.triggered.connect(self.setRightComp)

        self.exec_(position)

    def tr(self, string_to_translate):
        """
        Translate a string using the QCoreApplication translation framework
        @param string_to_translate: a unicode string
        @return: the translated unicode string if it was possible to translate
        """
        return str(QtCore.QCoreApplication.translate('MyDropDownMenu',
                                                           string_to_translate))

    def calcMenuDir(self):
        """
        This method returns the direction of the selected items. If there are
        different cutter directions in the selection 0 is returned, else
        1 for Left and 2 for right.
        """
        dir = self.selectedItems[0].cut_cor
        for item in self.selectedItems:
            if not(dir == item.cut_cor):
                return -1

        return dir-40

    def checkMenuDir(self, dir):
        """
        This method checks the buttons in the Contextmenu for the direction of
        the selected items.
        @param dir: The direction of the items -1=different, 0=None, 1=left, 2=right
        """
        self.noCompAction.setChecked(False)
        self.leCompAction.setChecked(False)
        self.reCompAction.setChecked(False)

        if dir == 0:
            self.noCompAction.setChecked(True)
        elif dir == 1:
            self.leCompAction.setChecked(True)
        elif dir == 2:
            self.reCompAction.setChecked(True)

    def invertSelection(self):
        """
        This function is called by the Contextmenu of the Graphicsview.
        @purpose: Inverts the selection of all shapes.
        """
        for shape in self.canvas_scene.shapes:
            shape.setSelected(not shape.isSelected())
            g.window.TreeHandler.updateShapeSelection(shape, shape.isSelected())
        self.canvas_scene.update()

    def disableSelection(self):
        """
        Disable all shapes which are currently selected. Based on the view
        options they are not shown, or showed in a different color
        """
        for shape in self.selectedItems:
            if shape.allowedToChange:
                shape.setDisable(True)
                g.window.TreeHandler.updateShapeEnabling(shape, False)
        self.canvas_scene.update()

    def enableSelection(self):
        """
        Enable all shapes which are currently selected. Based on the view
        options they are not shown, or showed in a different color
        """
        for shape in self.selectedItems:
            if shape.allowedToChange:
                shape.setDisable(False)
                g.window.TreeHandler.updateShapeEnabling(shape, True)
        self.canvas_scene.update()

    def switchDirection(self):
        """
        Switch the Direction of all items. For example from CW direction to CCW
        """
        for shape in self.selectedItems:
            shape.reverse()
            logger.debug(self.tr('Switched Direction at Shape Nr: %i') % shape.nr)
            self.canvas_scene.repaint_shape(shape)
        self.canvas_scene.update()
        g.window.TreeHandler.prepareExportOrderUpdate()

    def setNearestStPoint(self):
        """
        Search the nearest StartPoint to the clicked position of all selected shapes.
        """
        xyForZ = {}
        for shape in self.selectedItems:
            clicked = self.clicked
            if self.offset is not None:
                z = shape.axis3_start_mill_depth
                if z not in xyForZ:
                    clicked = xyForZ[z] = self.canvas_scene.determineSelectedPosition(self.clicked, z, self.offset)
            shape.setNearestStPoint(clicked)
            self.canvas_scene.repaint_shape(shape)
        self.canvas_scene.update()
        g.window.TreeHandler.prepareExportOrderUpdate()

    def setNoComp(self):
        """
        Sets the compensation to 40, which is none, for the selected shapes.
        """
        for shape in self.selectedItems:
            shape.cut_cor = 40
            logger.debug(self.tr('Changed Cutter Correction to None for shape: %i') % shape.nr)
            self.canvas_scene.repaint_shape(shape)
        self.canvas_scene.update()

    def setLeftComp(self):
        """
        Sets the compensation to 41, which is Left, for the selected shapes.
        """
        for shape in self.selectedItems:
            shape.cut_cor = 41
            logger.debug(self.tr('Changed Cutter Correction to left for shape: %i') % shape.nr)
            self.canvas_scene.repaint_shape(shape)
        self.canvas_scene.update()

    def setRightComp(self):
        """
        Sets the compensation to 42, which is Right, for the selected shapes.
        """
        for shape in self.selectedItems:
            shape.cut_cor = 42
            logger.debug(self.tr('Changed Cutter Correction to right for shape: %i') % shape.nr)
            self.canvas_scene.repaint_shape(shape)
        self.canvas_scene.update()
