# -*- coding: utf-8 -*-

############################################################################
#
#   Copyright (C) 2010-2014
#    Christian Kohl�ffel
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

import py2cv.globals.constants as c
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QGridLayout, QTextBrowser
from PyQt5.QtGui import QIcon, QPixmap, QTextCursor
from PyQt5 import QtCore

import logging

logger = logging.getLogger("Gui.AboutDialog")


class AboutDialog(QDialog):
    def __init__(self, title="Test", message="Test Text"):
        super(AboutDialog, self).__init__()

        self.title = title
        self.message = message

        self.initUI()

    def initUI(self):
        """
        initUI()
        """

        vbox = QVBoxLayout(self)
        grid1 = QGridLayout()
        grid1.setSpacing(10)

        self.text = QTextBrowser()
        self.text.setReadOnly(True)
        self.text.setOpenExternalLinks(True)
        self.text.append(self.message)
        self.text.moveCursor(QTextCursor.Start)
        self.text.ensureCursorVisible()

        vbox.addWidget(self.text)

        self.setLayout(vbox)
        self.setMinimumSize(550, 450)
        self.resize(550, 600)
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)
        self.setWindowTitle(self.title)
        iconWT = QIcon()
        iconWT.addPixmap(QPixmap(":images/DXF2GCODE-001.ico"),
                         QIcon.Normal, QIcon.Off)
        self.setWindowIcon(QIcon(iconWT))

        self.exec_()
