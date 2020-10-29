# -*- coding: utf-8 -*-

############################################################################
#
#   Copyright (C) 2010-2014
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

import py2cv.globals.constants as c
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QFrame, QGridLayout, QLabel, QLineEdit, QPushButton, QListWidget
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5 import QtCore


logger = logging.getLogger("Gui.PopUpDialog")


class PopUpDialog(QDialog):

    def __init__(self, title="Test", label='Value1', value=1.0, listMode=False):
        super(PopUpDialog, self).__init__()

        logger.debug(title)
        logger.debug(label)
        logger.debug(value)

        self.title = title
        self.label = label
        self.value = value

        self.result = None

        if not(len(label) == len(value)) and not listMode:
            raise Exception("Number of labels different to number of values")

        self.initUI(listMode)

    def tr(self, string_to_translate):
        """
        Translate a string using the QCoreApplication translation framework
        @param: string_to_translate: a unicode string
        @return: the translated unicode string if it was possible to translate
        """
        return str(QtCore.QCoreApplication.translate('PopUpDialog',
                                                           string_to_translate))

    def initUI(self, listMode):

        vbox = QVBoxLayout(self)

        top = QFrame(self)
        top.setFrameShape(QFrame.StyledPanel)

        bottom = QFrame(self)
        bottom.setFrameShape(QFrame.StyledPanel)

        grid1 = QGridLayout()
        grid1.setSpacing(10)
        self.lineLabel = []
        self.lineEdit = []
        self.listMode = listMode

        if not listMode:
            for i in range(len(self.label)):
                self.lineLabel.append(QLabel(self.label[i]))
                self.lineEdit.append(QLineEdit('%s' % self.value[i]))

                grid1.addWidget(self.lineLabel[i], i, 0)
                grid1.addWidget(self.lineEdit[i], i, 1)
        else:
            self.lineLabel = QListWidget()
            self.lineLabel.addItems(self.label)
            grid1.addWidget(self.lineLabel)

        top.setLayout(grid1)

        grid2 = QGridLayout()
        grid2.setSpacing(5)

        okButton = QPushButton(self.tr("OK"))
        cancelButton = QPushButton(self.tr("Cancel"))

        okButton.clicked.connect(self.cbOK)
        self.lineLabel.itemDoubleClicked.connect(self.cbOK)
        cancelButton.clicked.connect(self.cbCancel)

        grid2.addWidget(okButton, 0, 2)
        grid2.addWidget(cancelButton, 0, 3)

        bottom.setLayout(grid2)

        vbox.addWidget(top)
        vbox.addWidget(bottom)

        self.setLayout(vbox)

        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)
        self.setWindowTitle(self.title)
        iconWT = QIcon()
        iconWT.addPixmap(QPixmap(":images/opencv.ico"), QIcon.Normal, QIcon.Off)
        self.setWindowIcon(QIcon(iconWT))

        self.exec_()

    def cbOK(self):
        self.result = []
        if not self.listMode:
            for lineEdit in self.lineEdit:
                self.result.append(lineEdit.text())
        else:
            self.result = self.lineLabel.currentItem().text()
        logger.debug(self.result)
        self.close()

    def cbCancel(self):
        logger.debug('Cancel')
        self.close()

