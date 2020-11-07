# -*- coding: utf-8 -*-

############################################################################
#
#   Copyright (C) 2012-2015
#    Xavier Izard
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
This class is intended to deal with the drawing (.dxf) structure.
It has the following functions:
- populate the entities treeView and the layers treeView
- allow selection of shapes from any treeView and show the
  selection on the graphic view
- allow to enable/disable shapes from any treeView
- reflects into the treeView the changes that occurs on the graphic view
- set export order using drag & drop

@purpose: display tree structure of the .dxf file, select,
          enable and set export order of the shapes
"""

from __future__ import absolute_import

from math import degrees
import logging

import py2cv.globals.globals as g

from py2cv.core.shape import Shape

from py2cv.globals.helperfunctions import toInt, toFloat

import py2cv.globals.constants as c
from PyQt5.QtWidgets import QAction, QMenu, QWidget, QAbstractItemView
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5 import QtCore
isValid = lambda data: data
toPyObject = lambda data: data


class QVariantShape(QtCore.QVariant):
    """
    Wrapper is needed for PyQt5 since this version does not accept to add a QGraphisItem
     directly to a QStandardItem
    """
    def __init__(self, shapeobj):
        self.shapeobj = shapeobj


logger = logging.getLogger("Gui.TreeHandling")

# defines some arbitrary types for the objects stored into the treeView.
# These types will eg help us to find which kind of data is stored
# in the element received from a click() event
ENTITY_OBJECT = QtCore.Qt.UserRole + 1  # For storing refs to the entities elements (entities_list)
LAYER_OBJECT = QtCore.Qt.UserRole + 2  # For storing refs to the layers elements (layers_list)
SHAPE_OBJECT = QtCore.Qt.UserRole + 3  # For storing refs to the shape elements (entities_list & layers_list)
CUSTOM_GCODE_OBJECT = QtCore.Qt.UserRole + 4  # For storing refs to the custom gcode elements (layers_list)

PATH_OPTIMISATION_COL = 3  # Column that corresponds to TSP enable checkbox


class TreeHandler(QWidget):
    """
    Class to handle both QTreeView :  entitiesTreeView (for blocks, and the tree of blocks) and layersShapesTreeView (for layers and shapes)
    """

    def __init__(self, ui):
        """
        Standard method to initialize the class
        @param ui: the GUI
        """
        QWidget.__init__(self)
        self.ui = ui

        # Used to store previous values in order to enable/disable text
        #self.palette = self.ui.zRetractionArealLineEdit.palette()
        self.clearToolsParameters()

        # Layers & Shapes TreeView
        self.layer_item_model = None
        self.layers_list = None
        self.auto_update_export_order = False
        #self.ui.layersShapesTreeView.setExportOrderUpdateCallback(self.prepareExportOrderUpdate)
        #self.ui.layersShapesTreeView.setSelectionCallback(self.actionOnSelectionChange)  # pass the callback function to the QTreeView
        #self.ui.layersShapesTreeView.setKeyPressEventCallback(self.actionOnKeyPress)
        #self.ui.layersShapesTreeView.setSelectionMode(QAbstractItemView.ExtendedSelection)
        #self.ui.layersShapesTreeView.setSelectionBehavior(QAbstractItemView.SelectRows)

        #self.ui.layersGoUpPushButton.clicked.connect(self.ui.layersShapesTreeView.moveUpCurrentItem)
        #self.ui.layersGoDownPushButton.clicked.connect(self.ui.layersShapesTreeView.moveDownCurrentItem)

        # The layer/shape which is currently displayed in the parameters box
        self.display_tool_layer = None
        self.display_tool_shape = None

        # Don't change this line, the signal _must_ be "activated" (only activates on user action) and _not_ "currentIndexChanged" (activates programmatically and on user action)
        #self.ui.toolDiameterComboBox.activated[str].connect(self.toolUpdate)

        #self.ui.zRetractionArealLineEdit.editingFinished.connect(self.toolParameterzRetractionArealUpdate)
        #self.ui.zSafetyMarginLineEdit.editingFinished.connect(self.toolParameterzSafetyMarginUpdate)
        #self.ui.zInitialMillDepthLineEdit.editingFinished.connect(self.toolParameterzInitialMillDepthUpdate)
       # self.ui.zInfeedDepthLineEdit.editingFinished.connect(self.toolParameterzInfeedDepthUpdate)
        #self.ui.zFinalMillDepthLineEdit.editingFinished.connect(self.toolParameterzFinalMillDepthUpdate)
        #self.ui.g1FeedXYLineEdit.editingFinished.connect(self.toolParameterg1FeedXYUpdate)
        #self.ui.g1FeedZLineEdit.editingFinished.connect(self.toolParameterg1FeedZUpdate)

        # Entities TreeView
        self.entity_item_model = None
        self.entities_list = None
        self.ui.entitiesTreeView.setSelectionCallback(self.actionOnSelectionChange)  # pass the callback function to the QTreeView
        self.ui.entitiesTreeView.setKeyPressEventCallback(self.actionOnKeyPress)
        self.ui.entitiesTreeView.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.ui.entitiesTreeView.setSelectionBehavior(QAbstractItemView.SelectRows)

        self.ui.blocksCollapsePushButton.clicked.connect(self.expandToDepth0)
        self.ui.blocksExpandPushButton.clicked.connect(self.ui.entitiesTreeView.expandAll)

        # Build the contextual menu (mouse right click)
        self.context_menu = QMenu(self)
        #self.context_menu.addAction(QAction("Select all", self, triggered=self.ui.layersShapesTreeView.selectAll))
        #self.context_menu.addAction(QAction("Deselect all", self, triggered=self.ui.layersShapesTreeView.clearSelection))
        #self.context_menu.addSeparator()
        #self.context_menu.addAction(QAction("Enable selection", self, triggered=self.enableSelectedItems))
        #self.context_menu.addAction(QAction("Disable selection", self, triggered=self.disableSelectedItems))
        #self.context_menu.addSeparator()
        #self.context_menu.addAction(QAction("Optimize route for selection", self, triggered=self.optimizeRouteForSelectedItems))
        #self.context_menu.addAction(QAction("Don't opti. route for selection", self, triggered=self.doNotOptimizeRouteForSelectedItems))
        #self.context_menu.addSeparator()
        #self.context_menu.addAction(QAction("Remove custom GCode", self, triggered=self.removeCustomGCodeSelected))

        self.sub_menu = QMenu("Add custom GCode ...", self)
        # Save the exact name of the action, as is defined in the config file. Later on we use it to identify the action
        for custom_action in g.config.vars.Custom_Actions:
            menu_action = self.sub_menu.addAction(custom_action.replace('_', ' '))
            menu_action.setData(custom_action)

        self.context_menu.addMenu(self.sub_menu)

        # Right click menu
        #self.ui.layersShapesTreeView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        #self.ui.layersShapesTreeView.customContextMenuRequested.connect(self.displayContextMenu)

        # Not used for now, so hide them
        #self.ui.startAtXLabel.hide()
        #self.ui.startAtYLabel.hide()
        #self.ui.unitLabel_1.hide()
        #self.ui.unitLabel_2.hide()
       # self.ui.startAtXLineEdit.hide()
      #  self.ui.startAtYLineEdit.hide()
        
      #  self.ui.label_12.hide()
      #  self.ui.zRetractionArealLineEdit.hide()
       

    def tr(self, string_to_translate):
        """
        Translate a string using the QCoreApplication translation framework
        @param: string_to_translate: a unicode string
        @return: the translated unicode string if it was possible to translate
        """
        return str(QtCore.QCoreApplication.translate('TreeHandler',
                                                           string_to_translate))

    def updateConfiguration(self):
        """
        This function should be called each time the configuration changes. It updates tools and custom actions in the treeView
        If a tool or a custom action disapear from the configuration, it is removed from the treeview
        """
        # Load the tools from the config file to the tool selection combobox
        #self.ui.layersShapesTreeView.clearSelection()
        # Load the custom gcode names from the config file
        self.sub_menu.clear()
        for custom_action in g.config.vars.Custom_Actions:
            menu_action = self.sub_menu.addAction(custom_action.replace('_', ' '))
            menu_action.setData(custom_action)

        # update the items (if a tool or a custom_action disapeared from config file, we need to remove it in the treeview too)
        i = 0
        if self.layer_item_model: #  this is not set until buildLayerTree() is called
            i = self.layer_item_model.rowCount(QtCore.QModelIndex())

        while i > 0:
            i -= 1
            layer_item_index = self.layer_item_model.index(i, 0)

            if isValid(layer_item_index.data(LAYER_OBJECT)):
                real_layer = toPyObject(layer_item_index.data(LAYER_OBJECT))

                update_drawing = False
                if real_layer is not None and str(real_layer.tool_nr) not in g.config.vars.Tool_Parameters:
                    # The tool used for this layer doesn't exist anymore, we are going to replace it with the first tool
                    logger.warning("Tool {0} used for \"{1}\" layer doesn't exist anymore in the configuration ; using tool {2} instead".format(real_layer.tool_nr, real_layer.name, default_tool))
                    # Update the layer's tool and repaint
                    real_layer.tool_nr = default_tool # Tool 1 normally always exists
                    update_drawing = True

                if real_layer is not None\
                    and (real_layer.tool_diameter != g.config.vars.Tool_Parameters[str(real_layer.tool_nr)]['diameter']\
                      or real_layer.speed != g.config.vars.Tool_Parameters[str(real_layer.tool_nr)]['speed']\
                      or real_layer.start_radius != g.config.vars.Tool_Parameters[str(real_layer.tool_nr)]['start_radius']):
                    # The tool used for this layer exists, but its definition has changed, we need to update the layer
                    logger.warning("Tool {0} used for \"{1}\" layer has changed, updating layer's data".format(real_layer.tool_nr, real_layer.name))
                    real_layer.tool_diameter = g.config.vars.Tool_Parameters[str(real_layer.tool_nr)]['diameter']
                    real_layer.speed = g.config.vars.Tool_Parameters[str(real_layer.tool_nr)]['speed']
                    real_layer.start_radius = g.config.vars.Tool_Parameters[str(real_layer.tool_nr)]['start_radius']
                    update_drawing = True

                if update_drawing and g.window:
                    for shape in real_layer.shapes:
                        if isinstance(shape, Shape):
                            # Only repaint _real_ shapes (and not the custom GCode for example)
                            g.window.canvas_scene.repaint_shape(shape)
                    g.window.canvas_scene.update()

                # Assign the export order for the shapes of the layer "real_layer"
                for j in range(self.layer_item_model.rowCount(layer_item_index)):
                    shape_item_index = self.layer_item_model.index(j, 0, layer_item_index)

                    if isValid(shape_item_index.data(CUSTOM_GCODE_OBJECT)):
                        real_custom_action = toPyObject(shape_item_index.data(CUSTOM_GCODE_OBJECT))
                        if real_custom_action is not None and real_custom_action.name not in g.config.vars.Custom_Actions:
                            logger.warning("Custom action \"{0}\" used for \"{1}\" layer doesn't exist anymore in the configuration, removing it".format(real_custom_action.name, real_layer.name))
                            self.removeCustomGCode(shape_item_index)

    def displayContextMenu(self, position):
        pass

    def expandToDepth0(self):
        pass

    def buildLayerTree(self, layers_list):
        pass

    def AddShapeRowLayer(self, shape, parent_item):
        pass

    def AddCustomGCodeRowLayer(self, custom_gcode, parent_item, push_row=None):
        pass

    def buildEntitiesTree(self, entities_list):
        """
        This method populates the Entities (blocks) QTreeView with
        all the elements contained in the entities_list
        Method must be called each time a new .dxf file is loaded.
        options
        @param entities_list: list of the layers and shapes (created in the main)
        """

        self.entities_list = entities_list
        if self.entity_item_model:
            self.entity_item_model.clear()  # Remove any existing item_model
        self.entity_item_model = QStandardItemModel()
        self.entity_item_model.setHorizontalHeaderItem(0, QStandardItem(self.tr("[en]")))
        self.entity_item_model.setHorizontalHeaderItem(1, QStandardItem(self.tr("Name")))
        self.entity_item_model.setHorizontalHeaderItem(2, QStandardItem(self.tr("Value")))
        self.entity_item_model.setHorizontalHeaderItem(3, QStandardItem(self.tr("Note")))
        modele_root_element = self.entity_item_model.invisibleRootItem()

        if self.entities_list != None:
            self.buildEntitiesSubTree(modele_root_element, entities_list)

        # Signal to get events when a checkbox state changes (enable or disable shapes)
        self.entity_item_model.itemChanged.connect(self.on_itemChanged)

        self.ui.entitiesTreeView.setModel(self.entity_item_model)

        self.ui.entitiesTreeView.setSelectionMode(QAbstractItemView.SingleSelection)

        self.ui.entitiesTreeView.expandToDepth(0)

        for i in range(6):
            self.ui.entitiesTreeView.resizeColumnToContents(i)

    def buildEntitiesSubTree(self, elements_model, elements_list):
        """
        This method is called (possibly recursively) to populate the
        Entities treeView. It is not intended to be called directly,
        use buildEntitiesTree() function instead.
        options
        @param elements_model: the treeView model (used to store the data, see QT docs)
        @param elements_list: either a list of entities, or a shape
        @return (containsChecked, containsUnchecked) indicating whether the subtree contains checked and/or unchecked elements
        """
        containsChecked = False
        containsUnchecked = False
        if isinstance(elements_list, list):
            # We got a list
            for element in elements_list:
                (checked, unchecked) = self.addEntitySubTree(elements_model, element)
                containsChecked = containsChecked or checked
                containsUnchecked = containsUnchecked or unchecked
        else:
            # Unique element (shape)
            element = elements_list
            containsChecked, containsUnchecked = self.addEntitySubTree(elements_model, element)
        return containsChecked, containsUnchecked

    def addEntitySubTree(self, elements_model, element):
        """
        This method populates a row of the Entities treeView. It is
        not intended to be called directly, use buildEntitiesTree()
        function instead.
        options
        @param elements_model: the treeView model (used to store the data, see QT docs)
        @param element: the Entity or Shape element
        @return (containsChecked, containsUnchecked) indicating whether the subtree contains checked and/or unchecked elements
        """
        containsChecked = False
        containsUnchecked = False
        item_col_0 = None

        if hasattr(element,'children'):
            item_col_0 = QStandardItem()  # will only display a checkbox + an icon that will never be disabled
            item_col_0.setData(QtCore.QVariant(element), ENTITY_OBJECT)  # store a ref in our treeView element
            item_col_1 = QStandardItem(element.name)
            item_col_2 = QStandardItem()
            item_col_3 = QStandardItem()
            elements_model.appendRow([item_col_0, item_col_1, item_col_2, item_col_3])
            (checked, unchecked) = self.buildEntitiesSubTree(item_col_0, element.children)
            containsChecked = containsChecked or checked
            containsUnchecked = containsUnchecked or unchecked
            #element.enable = 1
        else:
            #children
            item_col_0 = QStandardItem()  # will only display a checkbox + an icon that will never be disabled
            #item_col_0.setData(QtCore.QVariant(element), SHAPE_OBJECT)  # store a ref in our treeView element
            item_col_1 = QStandardItem(element.name)
            item_col_2 = QStandardItem(str(element.value))
            item_col_3 = QStandardItem(element.note)
            elements_model.appendRow([item_col_0, item_col_1, item_col_2, item_col_3])

        flags = QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled

        if hasattr(element,'children'):
            if element.enable:
                item_col_0.setCheckState(QtCore.Qt.Checked)
            else:
                item_col_0.setCheckState(QtCore.Qt.Unchecked)
            item_col_0.setFlags(flags | QtCore.Qt.ItemIsUserCheckable)
        else:
            item_col_0.setFlags(flags)
        
        item_col_1.setFlags(flags)

        if hasattr(element,'children'):
            item_col_2.setFlags(flags)
        else:
            item_col_2.setFlags(flags | QtCore.Qt.ItemIsEditable)

        item_col_3.setFlags(flags)

        return (containsChecked, containsUnchecked)

    def getCheckState(self, containsChecked, containsUnchecked):
        if containsChecked:
            if containsUnchecked:
                return QtCore.Qt.PartiallyChecked
            else:
                return QtCore.Qt.Checked
        else:
            return QtCore.Qt.Unchecked

    def updateExportOrder(self, includeDisableds=False):
        pass
        
    def updateTreeViewOrder(self):
        pass

    def columnsSelectDeselect(self, selection_model, item_index, select):
        pass

    def updateShapeSelection(self, shape, select):
        pass

    def updateShapeEnabling(self, shape, enable):
        pass

    def findLayerItemIndexFromShape(self, shape):
        pass

    def findEntityItemIndexFromShape(self, shape):
        pass

    def traverseChildrenAndFindShape(self, item_model, item_index, shape):
        pass

    def traverseChildrenAndSelect(self, item_model, item_index, state):
        pass

    def traverseChildrenAndEnableDisable(self, item_model, item_index, checked_state):
        pass

    def traverseParentsAndUpdateEnableDisable(self, item_model, item_index):
        pass

    def toolUpdate(self):
        pass

    def toolParameterzRetractionArealUpdate(self):
        pass

    def toolParameterzSafetyMarginUpdate(self):
        pass

    def toolParameterzInfeedDepthUpdate(self):
        pass

    def toolParameterg1FeedXYUpdate(self):
        pass

    def toolParameterg1FeedZUpdate(self):
        pass

    def toolParameterzInitialMillDepthUpdate(self):
        pass

    def toolParameterzFinalMillDepthUpdate(self):
        pass

    def actionOnSelectionChange(self, parent, selected, deselected):
        pass

    def updateSelection(self, treeview):
        pass

    def updateSelectionRecursive(self, model, root, item_sel, item_desel):
        pass

    def clearToolsParameters(self):
        pass

    def updateToolParameters(self):
        pass

    def displayToolParametersForItem(self, layer_item, shape_item = None):
        pass

    def updateAndColorizeWidget(self, widget, previous_value, value):
        pass

    def disableSelectedItems(self):
        pass

    def enableSelectedItems(self):
        pass

    def doNotOptimizeRouteForSelectedItems(self):
        pass

    def optimizeRouteForSelectedItems(self):
        pass

    def actionOnKeyPress(self, event):
        pass

    def on_selectionChanged(self, item):
        aa = item.row()
        return

    def on_itemChanged(self, item):
        """
        This slot is called when some data changes in one of the
        TreeView. For us, since rows are read only, it is only
        triggered when a checkbox is checked/unchecked
        options
        @param item: item is the modified element. It can be a Shape, a Layer or an Entity
        """

        if item.data(ENTITY_OBJECT) != None:
            # Checkbox concerns an Entity object => check/uncheck each sub-items (shapes and/or other entities)
            self.traverseChildrenAndEnableDisable(self.entity_item_model, item.index(), item.checkState())
            self.entities_list[item.row()].enable = item.checkState()
        else:
            #value modified
            stype = type(self.entities_list[item.parent().row()].children[item.row()].value)
            if stype is int:
                self.entities_list[item.parent().row()].children[item.row()].value = int(float(item.text()))
            elif stype is float:
                self.entities_list[item.parent().row()].children[item.row()].value = float(item.text())
        
        g.window.updateOpencv()

    def updateCheckboxOfItem(self, item, check):
        pass

    def enableDisableTreeRow(self, item, check):
        pass


    def removeCustomGCodeSelected(self):
        pass

    def removeCustomGCode(self, shape_item_index = None):
        pass

    def addCustomGCodeAfter(self, action_name):
        pass

    def prepareExportOrderUpdate(self):
        pass

    def setLiveUpdateExportRoute(self, live_update):
        pass
