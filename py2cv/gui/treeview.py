# -*- coding: utf-8 -*-

############################################################################
#
#   Copyright (C) 2012-2014
#    Xavier Izard
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
TreeView class is a subclass of QT QTreeView class.
Subclass is done in order to:
- implement a simple (ie not complex) drag & drop
- get selection events
@newfield purpose: Purpose
@newfield sideeffect: Side effect, Side effects

@purpose: display tree structure of the .dxf file, select,
          enable and set export order of the shapes
"""

import py2cv.globals.constants as c
from PyQt5.QtWidgets import QTreeView
from PyQt5.QtGui import QStandardItemModel
from PyQt5 import QtCore


class TreeView(QTreeView):
    """
    Subclassed QTreeView to match our needs.
    Implement a simple (ie not complex) drag & drop, get selection events
    """

    def __init__(self, parent = None):
        """
        Initialization of the TreeView class.
        """
        QTreeView.__init__(self, parent)

        self.dragged_element = False #No item is currently dragged & dropped
        self.dragged_element_model_index = None
        self.selectionChangedcallback = None
        self.keyPressEventcallback = None
        self.signals_blocked = False #Transmit events between classes

        self.pressed.connect(self.elementPressed)

    def setExportOrderUpdateCallback(self, callback):
        self.exportOrderUpdateCallback = callback

    def setSelectionCallback(self, callback):
        """
        Register a callback function called when the selection changes
        on the TreeView options
        @param callback: function with prototype functionName(parent, selected, deselected):
        """
        self.selectionChangedcallback = callback

    def setKeyPressEventCallback(self, callback):
        """
        Register a callback function called when a key is pressed on the TreeView
        @param callback: function with prototype : accepted functionName(key_code, item_index):
        """
        self.keyPressEventcallback = callback

    def dragEnterEvent(self, event):
        """
        Set flag dragged_element to True (we have started a drag).
        Note: we can't get the dragged index from this function because
        it is called really late in the drag chain. If the user is too
        fast in drag & drop, then the event.pos() will return a position
        that is sensibly different from the original position when the user
        started to drag the item. So we only store a flag. We already
        got the item dragged through the elementPressed() function.
        options
        @param event: the dragEvent (contains position, ...)
        print("\033[32;1mdragEnterEvent {0} at pos({1}), index = {2}\033[m\n".format(event, event.pos(), self.indexAt(event.pos()).parent().internalId()))
        """
        self.dragged_element = True
        event.acceptProposedAction()

    def elementPressed(self, element_model_index):
        """
        This function is called when an element (Shape, ...) is pressed
        with the mouse. It aims to store the index (QModelIndex) of
        the element pressed.
        options
        @param element_model_index: QModelIndex of the element pressed
        print("\033[32melementPressed row = {0}\033[m".format(element_model_index.model().itemFromIndex(element_model_index).row()))
        """
        #save the index of the clicked element...
        self.dragged_element_model_index = element_model_index

    def dropEvent(self, event):
        """
        This function is called when the user has released the mouse
        button to drop an element at the mouse pointer location.
        Note: we have totally reimplemented this function because the
        default QT implementation wants to Copy & Delete each dragged
        item, even when we only use internals move inside the treeView.
        This is totally unnecessary and over-complicated for us because
        it would imply to implement a QMimeData import and export
        functions to export our Shapes / Layers / Entities. The code
        below tries to move the items to the right place when they are
        dropped ; it uses simple lists permutations (ie no duplicates
        & deletes).
        options
        @param event: the dropEvent (contains position, ...)
        print("\033[32mdropEvent {0} at pos({1}).{3}, index = {2}\033[m\n".format(event, event.pos(), self.indexAt(event.pos()).parent().internalId(), self.dropIndicatorPosition()))
        """

        if self.dragged_element and self.dragged_element_model_index:
            #print("action proposee = {0}".format(event.proposedAction()))
            event.setDropAction(QtCore.Qt.IgnoreAction)
            event.accept()

            drag_item = self.dragged_element_model_index.model().itemFromIndex(self.dragged_element_model_index)
            items_parent = drag_item.parent()
            if not items_parent:
                #parent is 0, so we need to get the root item of the tree as parent...
                items_parent = drag_item.model().invisibleRootItem()
            drop_model_index = self.indexAt(event.pos())
            # Get the insert position related to the drop item:
            # OnItem, AboveItem, BelowItem, OnViewport...
            relative_position = self.dropIndicatorPosition()

            #compute the new position of the layer or the shape
            if drop_model_index.isValid() and relative_position != QTreeView.OnViewport:
                #drop position is computable from a real element
                drop_item = drop_model_index.model().itemFromIndex(drop_model_index)

                if drag_item.parent() == drop_item.parent():
                    #dropped element is on the same tree branch as
                    #dragged element...
                    drag_row = self.dragged_element_model_index.row() #original row
                    #destination row (+1 if relative pos is below the drop element)...
                    drop_row = drop_model_index.row() + (1 if relative_position == QTreeView.BelowItem else 0)
                    #print("\033[32;1mACCEPTED!\033[m\n")

                elif (drag_item.parent() == drop_item or not drop_item.parent()\
                  and drag_item.parent() == drop_item.model().invisibleRootItem().child(drop_item.row(), 0))\
                  and (relative_position == QTreeView.BelowItem or relative_position == QTreeView.OnItem):
                    #we are on parent item (second test takes the first column
                    # of the drop_item's row. First column is where child are
                    # inserted, so we must compare with this col)

                    # original row...
                    drag_row = self.dragged_element_model_index.row()
                    # destination row is 0 because item is dropped on the parent...
                    drop_row = 0
                    #print("\033[32;1mACCEPTED ON PARENT!\033[m\n")
                elif (not drop_item.parent() and self.dragged_element_model_index.parent().sibling(self.dragged_element_model_index.parent().row()+1, 0) == drop_item.model().invisibleRootItem().child(drop_item.row(), 0).index())\
                 and (relative_position == QTreeView.AboveItem or relative_position == QTreeView.OnItem):
                    #we are on next parent item => insert at end of the dragged item's layer
                    # original row...
                    drag_row = self.dragged_element_model_index.row()
                    # insert at end...
                    drop_row = items_parent.rowCount()
                    #print("\033[32;1mACCEPTED ON NEXT PARENT!\033[m\n")

                else:
                    #we are in the wrong branch of the tree,
                    # item can't be pasted here
                    drop_row = -1
                    #print("\033[31;1mREFUSED!\033[m\n")

            else:
                #We are below any tree element => insert at end
                drag_row = self.dragged_element_model_index.row() #original row
                drop_row = items_parent.rowCount() #insert at end
                #print("\033[32;1mACCEPTED AT END!\033[m\n")

            #effectively move the item
            if drop_row >= 0:
                #print("from row {0} to row {1}".format(drag_row, drop_row))

                item_to_be_moved = items_parent.takeRow(drag_row)
                if drop_row > drag_row:
                    #we have one less item in the list, so if the item is
                    # dragged below its original position, we must
                    # correct its insert position
                    drop_row -= 1
                items_parent.insertRow(drop_row, item_to_be_moved)

                if not self.signals_blocked:
                    # Signal that the order of the TreeView has changed...
                    self.exportOrderUpdateCallback()

            self.dragged_element = False
        else:
            event.ignore()

    def moveUpCurrentItem(self):
        """
        Move the current item up. This slot aims to be connected to a button.
        If there is no current item, do nothing.
        """
        current_item_index = self.currentIndex()
        if current_item_index and current_item_index.isValid():
            current_item = current_item_index.model().itemFromIndex(current_item_index)
            current_item_parent = current_item.parent()
            if not current_item_parent:
                #parent is 0, so we need to get the root item of the tree as parent...
                current_item_parent = current_item.model().invisibleRootItem()

            pop_row = current_item_index.row() #original row
            push_row = pop_row - 1
            if push_row >= 0:
                item_to_be_moved = current_item_parent.takeRow(pop_row)
                current_item_parent.insertRow(push_row, item_to_be_moved)
                self.setCurrentIndex(current_item.index())

                if not self.signals_blocked:
                    # Signal that the order of the TreeView has changed
                    self.exportOrderUpdateCallback()

    def moveDownCurrentItem(self):
        """
        Move the current item down. This slot aims to be connected to a button.
        If there is no current item, do nothing.
        """
        current_item_index = self.currentIndex()
        if current_item_index and current_item_index.isValid():
            current_item = current_item_index.model().itemFromIndex(current_item_index)
            current_item_parent = current_item.parent()
            if not current_item_parent:
                #parent is 0, so we need to get the root item of the tree as parent...
                current_item_parent = current_item.model().invisibleRootItem()

            pop_row = current_item_index.row() #original row
            push_row = pop_row + 1
            if push_row < current_item_parent.rowCount():
                item_to_be_moved = current_item_parent.takeRow(pop_row)
                current_item_parent.insertRow(push_row, item_to_be_moved)
                self.setCurrentIndex(current_item.index())

                if not self.signals_blocked:
                    # Signal that order of the TreeView has changed...
                    self.exportOrderUpdateCallback()

    def blockSignals(self, block):
        """
        Blocks the signals from this class. Subclassed in order to also block
        selectionChanged "signal" (callback) options
        @param block: whether to block signal (True) or not (False)
        """
        self.signals_blocked = block
        QTreeView.blockSignals(self, block)

    def selectionChanged(self, selected, deselected):
        """
        Function called by QT when the selection has changed for this treeView.
        Subclassed in order to call a callback function options
        @param selected: list of selected items
        @param deselected: list of deselected items
        print("\033[32;1mselectionChanged selected count = {0} ; deselected count = {1}\033[m".format(selected.count(), deselected.count()))
        """
        pass

    def keyPressEvent(self, keyEvent):
        """
        Function called by QT when a key has been pressed inside the treeView.
        Subclassed in order to call a callback function
        @param keyEvent: keyboard event
        print("\033[31;1mkeyPressEvent() key = {0}\033[m".format(keyEvent.key()))
        """

        if self.keyPressEventcallback and not self.signals_blocked:
            if not self.keyPressEventcallback(keyEvent):
                # key not accepted => send it back to the parent
                QTreeView.keyPressEvent(self, keyEvent)
        else:
            QTreeView.keyPressEvent(self, keyEvent)



class MyStandardItemModel(QStandardItemModel):
    """
    Subclass QStandardItemModel to avoid error while using Drag & Drop
    """

    def __init__(self, parent = None):
        """
        Initialization of the MyStandardItemModel class.
        """
        QStandardItemModel.__init__(self, parent)

    def mimeData(self, indexes):
        """
        This function is called by QT each time a drag operation is
        initiated, to serialize the data associated with the
        dragged item. However, QT doesn't know how to serialize a Shape
        or a Layer, so it throws an error ... since we handle Drag & Drop
        internally, we don't need any serialization, so we subclass
        the function and return nothing (trick to avoid errors).
        """
        mimeData = QtCore.QMimeData()
        #mimeData.setData("application/x-qabstractitemmodeldatalist", "")
        #mimeData.setData("application/x-qstandarditemmodeldatalist", "")
        #mimeData.setData("application/x-qstandarditemmodeldatalist",0)

        return mimeData
