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

"""
Special purpose canvas including all required plotting function etc.

@purpose:  Plotting all
"""

from __future__ import absolute_import
from __future__ import division

import logging

from py2cv.core.point import Point
from py2cv.core.shape import Shape
from py2cv.core.boundingbox import BoundingBox
from py2cv.gui.wpzero import WpZero
from py2cv.gui.canvas import CanvasBase, MyDropDownMenu

import py2cv.globals.globals as g

from PyQt5.QtWidgets import QGraphicsItem, QGraphicsView, QRubberBand, QGraphicsScene
from PyQt5.QtGui import QPen, QPainterPathStroker, QImage, QPixmap
from PyQt5 import QtCore


logger = logging.getLogger("DxfImport.myCanvasClass")


class MyGraphicsView(CanvasBase):
    """
    This is the used Canvas to print the graphical interface of dxf2gcode.
    All GUI things should be performed in the View and plotting functions in
    the scene
    """

    def __init__(self, parent=None):
        """
        Initialisation of the View Object. This is called by the gui created
        with the QTDesigner.
        @param parent: Main is passed as a pointer for reference.
        """
        super(MyGraphicsView, self).__init__(parent)
        self.currentItem = None

        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorViewCenter)

        self.setDragMode(QGraphicsView.NoDrag)

        self.parent = parent
        self.mppos = None

        self.rubberBand = QRubberBand(QRubberBand.Rectangle, self)
        self.prvRectRubberBand = QtCore.QRect()

    def tr(self, string_to_translate):
        """
        Translate a string using the QCoreApplication translation framework
        @param string_to_translate: a unicode string
        @return: the translated unicode string if it was possible to translate
        """
        return str(QtCore.QCoreApplication.translate('MyGraphicsView',
                                                           string_to_translate))

    def contextMenuEvent(self, event):
        """
        Create the contextmenu.
        @purpose: Links the new Class of ContextMenu to Graphicsview.
        """
        position = self.mapToGlobal(event.pos())
        GVPos = self.mapToScene(event.pos())
        real_pos = Point(GVPos.x(), -GVPos.y())

        menu = MyDropDownMenu(self.scene(), position, real_pos)

    def wheelEvent(self, event):
        """
        With Mouse Wheel the object is scaled
        @purpose: Scale by mouse wheel
        @param event: Event Parameters passed to function
        """
        delta = event.angleDelta().y()
        scale = (1000 + delta) / 1000.0
        self.scale(scale, scale)

    def mousePressEvent(self, event):
        """
        Right Mouse click shall have no function, Therefore pass only left
        click event
        @purpose: Change inherited mousePressEvent
        @param event: Event Parameters passed to function
        """

        if self.dragMode() == 1:
            super(MyGraphicsView, self).mousePressEvent(event)
        elif event.button() == QtCore.Qt.LeftButton:
            self.mppos = event.pos()
        else:
            pass

    def mouseReleaseEvent(self, event):
        """
        Right Mouse click shall have no function, Therefore pass only left
        click event
        @purpose: Change inherited mousePressEvent
        @param event: Event Parameters passed to function
        """

        if self.dragMode() == 1:
            super(MyGraphicsView, self).mouseReleaseEvent(event)
        else:
            self.rubberBand.hide()
            pass
        self.mppos = None

    def mouseMoveEvent(self, event):
        """
        MouseMoveEvent of the Graphiscview. May also be used for the Statusbar.
        @purpose: Get the MouseMoveEvent and use it for the Rubberband Selection
        @param event: Event Parameters passed to function
        """
        if self.mppos is not None:
            Point = event.pos() - self.mppos
            if Point.manhattanLength() > 3:
                # print 'the mouse has moved more than 3 pixels since the oldPosition'
                # print "Mouse Pointer is currently hovering at: ", event.pos()
                rect = QtCore.QRect(self.mppos, event.pos())
                '''
                The following is needed because of PyQt5 doesn't like to switch from sign
                 it will keep displaying last rectangle, i.e. you can end up will multiple rectangles
                '''
                if self.prvRectRubberBand.width() > 0 and not rect.width() > 0 or rect.width() == 0 or\
                   self.prvRectRubberBand.height() > 0 and not rect.height() > 0 or rect.height() == 0:
                    self.rubberBand.hide()
                self.rubberBand.setGeometry(rect.normalized())
                self.rubberBand.show()
                self.prvRectRubberBand = rect

        scpoint = self.mapToScene(event.pos())

        # self.setStatusTip('X: %3.1f; Y: %3.1f' % (scpoint.x(), -scpoint.y()))
        # works not as supposed to
        self.setToolTip('X: %3.1f; Y: %3.1f' %(scpoint.x(), -scpoint.y()))

        super(MyGraphicsView, self).mouseMoveEvent(event)

    def autoscale(self):
        """
        Automatically zooms to the full extend of the current GraphicsScene
        """
        scene = self.scene()
        width = scene.BB.Pe.x - scene.BB.Ps.x
        height = scene.BB.Pe.y - scene.BB.Ps.y
        scext = QtCore.QRectF(scene.BB.Ps.x, -scene.BB.Pe.y, width * 1.05, height * 1.05)
        self.fitInView(scext, QtCore.Qt.KeepAspectRatio)
        logger.debug(self.tr("Autoscaling to extend: %s") % scext)

    def setShowPathDirections(self, flag):
        """
        This function is called by the Main Window from the Menubar.
        @param flag: This flag is true if all Path Direction shall be shown
        """
        scene = self.scene()
        for shape in scene.shapes:
            #shape.starrow.setallwaysshow(flag)
            shape.enarrow.setallwaysshow(flag)
            shape.stmove.setallwaysshow(flag)

    def resetAll(self):
        """
        Deletes the existing GraphicsScene.
        """
        scene = self.scene()
        del scene

class MyGraphicsScene(QGraphicsScene):
    """
    This is the Canvas used to print the graphical interface of dxf2gcode.
    The Scene is rendered into the previously defined mygraphicsView class.
    All performed plotting functions should be defined here.
    @sideeffect: None
    """
    def __init__(self):
        QGraphicsScene.__init__(self)

        self.shapes = []
        self.wpzero = None
        self.routearrows = []
        self.routetext = []
        self.expprv = None
        self.expcol = None
        self.expnr = 0

        self.showDisabledPaths = False

        self.BB = BoundingBox()

    def tr(self, string_to_translate):
        """
        Translate a string using the QCoreApplication translation framework
        @param string_to_translate: a unicode string
        @return: the translated unicode string if it was possible to translate
        """
        return str(QtCore.QCoreApplication.translate('MyGraphicsScene',
                                                           string_to_translate))

    def plotAll(self, shapes):
        """
        Instance is called by the Main Window after the defined file is loaded.
        It generates all ploting functionality. The parameters are generally
        used to scale or offset the base geometry (by Menu in GUI).
        """
        if len(shapes.imglist) > 1:
            # Automatic check format
            image = shapes.imglist[len(shapes.imglist)-1]
            qformat = QImage.Format_Indexed8
            if len(image.shape) == 3:
                if image.shape[2] == 4:
                    qformat = QImage.Format_RGBA8888
                else:
                    qformat = QImage.Format_RGB888
            self.qImg = QImage(image.data, image.shape[1], image.shape[0], image.strides[0], qformat).rgbSwapped()
        else:
            # If original image, need rgbswap
            image = shapes.imglist[0]
            self.qImg = QImage(image.data, image.shape[1], image.shape[0], image.strides[0], QImage.Format_RGB888).rgbSwapped()

        self.BB.Pe.x = image.shape[1]
        self.BB.Pe.y = image.shape[0]

        self.addPixmap(QPixmap(self.qImg))
        self.draw_wp_zero()
        self.update()

    def repaint_shape(self, shape):
        # setParentItem(None) might let it crash, hence we rely on the garbage collector
        shape.stmove.hide()
        shape.starrow.hide()
        shape.enarrow.hide()
        del shape.stmove
        del shape.starrow
        del shape.enarrow
        self.paint_shape(shape)
        if not shape.isSelected():
            shape.stmove.hide()
            shape.starrow.hide()
            shape.enarrow.hide()

    def paint_shape(self, shape):
        pass

    def draw_wp_zero(self):
        """
        This function is called while the drawing of all items is done. It plots
        the WPZero to the Point x=0 and y=0. This item will be enabled or
        disabled to be shown or not.
        """
        self.wpzero = WpZero(QtCore.QPointF(0, 0))
        self.addItem(self.wpzero)

    def createstarrow(self, shape):
        pass

    def createenarrow(self, shape):
        pass

    def createstmove(self, shape):
        pass

    def delete_opt_paths(self):
        pass

    def addexproutest(self):
        pass

    def addexproute(self, exp_order, layer_nr):
        pass

    def addexprouteen(self):
        pass

    def setShowDisabledPaths(self, flag):
        pass

class ShapeGUI(QGraphicsItem, Shape):
    PEN_NORMAL = QPen(QtCore.Qt.black, 1, QtCore.Qt.SolidLine)
    PEN_NORMAL.setCosmetic(True)
    PEN_SELECT = QPen(QtCore.Qt.red, 2, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin)
    PEN_SELECT.setCosmetic(True)
    PEN_NORMAL_DISABLED = QPen(QtCore.Qt.gray, 1, QtCore.Qt.DotLine)
    PEN_NORMAL_DISABLED.setCosmetic(True)
    PEN_SELECT_DISABLED = QPen(QtCore.Qt.blue, 1, QtCore.Qt.DashLine)
    PEN_SELECT_DISABLED.setCosmetic(True)
    PEN_BREAK = QPen(QtCore.Qt.magenta, 1, QtCore.Qt.SolidLine)
    PEN_BREAK.setCosmetic(True)
    PEN_LEFT = QPen(QtCore.Qt.darkCyan, 1, QtCore.Qt.SolidLine)
    PEN_LEFT.setCosmetic(True)
    PEN_RIGHT = QPen(QtCore.Qt.darkMagenta, 1, QtCore.Qt.SolidLine)
    PEN_RIGHT.setCosmetic(True)

    def __init__(self, nr, closed, parentEntity):
        QGraphicsItem.__init__(self)
        Shape.__init__(self, nr, closed, parentEntity)

        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setAcceptedMouseButtons(QtCore.Qt.NoButton)

        self.selectionChangedCallback = None
        self.enableDisableCallback = None

        self.starrow = None
        self.enarrow = None

    def __str__(self):
        return super(ShapeGUI, self).__str__()

    def tr(self, string_to_translate):
        return super(ShapeGUI, self).tr(string_to_translate)

    def contains_point(self, point):
        """
        Method to determine the minimal distance from the point to the shape
        @param point: a QPointF
        @return: minimal distance
        """
        min_distance = float(0x7fffffff)
        ref_point = Point(point.x(), point.y())
        t = 0.0
        while t < 1.0:
            per_point = self.path.pointAtPercent(t)
            spline_point = Point(per_point.x(), per_point.y())
            distance = ref_point.distance(spline_point)
            if distance < min_distance:
                min_distance = distance
            t += 0.01
        return min_distance

    def setSelectionChangedCallback(self, callback):
        """
        Register a callback function in order to inform parents when the selection has changed.
        Note: we can't use QT signals here because ShapeClass doesn't inherits from a QObject
        @param callback: the function to be called, with the prototype callbackFunction(shape, select)
        """
        self.selectionChangedCallback = callback

    def setEnableDisableCallback(self, callback):
        """
        Register a callback function in order to inform parents when a shape has been enabled or disabled.
        Note: we can't use QT signals here because ShapeClass doesn't inherits from a QObject
        @param callback: the function to be called, with the prototype callbackFunction(shape, enabled)
        """
        self.enableDisableCallback = callback

    def setPen(self, pen):
        """
        Method to change the Pen of the outline of the object and update the
        drawing
        """
        self.pen = pen

    def paint(self, painter, option, widget):
        """
        Method will be triggered with each paint event. Possible to give options
        @param painter: Reference to std. painter
        @param option: Possible options here
        @param widget: The widget which is painted on.
        """
        if self.isSelected() and not self.isDisabled():
            painter.setPen(ShapeGUI.PEN_SELECT)
        elif not self.isDisabled():
            if self.parentLayer.isBreakLayer():
                painter.setPen(ShapeGUI.PEN_BREAK)
            elif self.cut_cor == 41:
                painter.setPen(ShapeGUI.PEN_LEFT)
            elif self.cut_cor == 42:
                painter.setPen(ShapeGUI.PEN_RIGHT)
            else:
                painter.setPen(ShapeGUI.PEN_NORMAL)
        elif self.isSelected():
            painter.setPen(ShapeGUI.PEN_SELECT_DISABLED)
        else:
            painter.setPen(ShapeGUI.PEN_NORMAL_DISABLED)

        painter.drawPath(self.path)

    def boundingRect(self):
        """
        Required method for painting. Inherited by Painterpath
        @return: Gives the Bounding Box
        """
        return self.path.boundingRect()

    def shape(self):
        """
        Reimplemented function to select outline only.
        @return: Returns the Outline only
        """
        painterStrock = QPainterPathStroker()
        painterStrock.setCurveThreshold(0.01)
        painterStrock.setWidth(0)

        stroke = painterStrock.createStroke(self.path)
        return stroke

    def setSelected(self, flag=True, blockSignals=True):
        """
        Override inherited function to turn off selection of Arrows.
        @param flag: The flag to enable or disable Selection
        """
        #self.starrow.setSelected(flag)
        self.enarrow.setSelected(flag)
        self.stmove.setSelected(flag)

        QGraphicsItem.setSelected(self, flag)
        Shape.setSelected(self, flag)

        if self.selectionChangedCallback and not blockSignals:
            self.selectionChangedCallback(self, flag)

    def setDisable(self, flag=False, blockSignals=True):
        """
        New implemented function which is in parallel to show and hide.
        @param flag: The flag to enable or disable Selection
        """
        # QGraphicsItem.setDisable(self, flag)
        Shape.setDisable(self, flag)
        scene = self.scene()

        if scene is not None:
            if not scene.showDisabledPaths and flag:
                self.hide()
                #self.starrow.setSelected(False)
                self.enarrow.setSelected(False)
                self.stmove.setSelected(False)
            else:
                self.show()

        if self.enableDisableCallback and not blockSignals:
            self.enableDisableCallback(self, not flag)

