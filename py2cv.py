#!/usr/bin/env python3
# -*- coding: utf-8 -*-

############################################################################
#
#   Copyright (C) 2010-2016
#    Christian Kohlöffel
#    Jean-Paul Schouwstra
#
#   This file is part of py2cv.
#
#   py2cv is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   py2cv is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with py2cv.  If not, see <http://www.gnu.org/licenses/>.
#
############################################################################

from __future__ import absolute_import
from __future__ import division

import argparse
import logging
import os
import sys
import time
import cv2
import numpy as np

import py2cv.globals.constants as c
import py2cv.globals.globals as g
from py2cv.core.layercontent import Layers
from py2cv.core.project import Project
from py2cv.globals.config import MyConfig
from py2cv.globals.helperfunctions import qstr_encode, str_decode, str_encode
from py2cv.globals.logger import LoggerClass
from py2cv.gui.aboutdialog import AboutDialog
from py2cv.gui.configwindow import ConfigWindow
from py2cv.gui.popupdialog import PopUpDialog
from py2cv.gui.treehandling import TreeHandler
from copy import deepcopy

from PyQt5.QtWidgets import QMainWindow, QGraphicsView, QFileDialog, QApplication, QMessageBox
from PyQt5 import QtCore
from PyQt5.QtNetwork import QTcpServer, QHostAddress
getOpenFileName = QFileDialog.getOpenFileName
getSaveFileName = QFileDialog.getSaveFileName

logger = logging.getLogger()

#g.folder = os.path.join(os.path.expanduser("~"), ".config/py2cv").replace("\\", "/")
#for local config floder
g.folder = os.path.join(os.getcwd(), ".config").replace("\\", "/")

class MainWindow(QMainWindow):

    """
    Main Class
    """

    # Define a QT signal that is emitted when the configuration changes.
    # Connect to this signal if you need to know when the configuration has
    # changed.
    configuration_changed = QtCore.pyqtSignal()

    def __init__(self, app):
        """
        Initialization of the Main window. This is directly called after the
        Logger has been initialized. The Function loads the GUI, creates the
        used Classes and connects the actions to the GUI.
        """
        QMainWindow.__init__(self)

        # Build the configuration window
        self.config_window = ConfigWindow(g.config.makeConfigWidgets(),
                                          g.config.var_dict,
                                          g.config.var_dict.configspec,
                                          self)
        self.config_window.finished.connect(self.updateConfiguration)

        self.app = app
        self.settings = QtCore.QSettings("py2cv", "py2cv")

        self.ui = Ui_MainWindow()

        self.ui.setupUi(self)
        self.showMaximized()

        self.cameraEnable = False

        self.canvas = self.ui.canvas
        self.canvas_scene = None

        self.TreeHandler = TreeHandler(self.ui)
        self.configuration_changed.connect(self.TreeHandler.updateConfiguration)

        if sys.version_info[0] == 2:
            error_message = QMessageBox(QMessageBox.Critical, 'ERROR', self.tr("Python version 2 is not supported, please use it with python version 3."))
            sys.exit(error_message.exec_())

        self.d2g = Project(self)

        self.createActions()
        self.connectToolbarToConfig()

        self.filename = ""

        # TCP Server
        if g.config.vars.Trigger.tcp_server_enable:
            self.server = QTcpServer()
            self.server.listen(QHostAddress.Any,int(g.config.vars.Trigger.tcp_server_port))
            # Connection connect
            self.server.newConnection.connect(self.on_newConnection)
        self.entityRoot = None
        self.layerContents = Layers([])

        self.cont_dx = 0.0
        self.cont_dy = 0.0
        self.cont_rotate = 0.0
        self.cont_scale = 1.0

        self.restoreWindowState()

        if g.config.vars.AutoStart.autostart_enable:
            self.filename = qstr_encode(g.config.vars.AutoStart.autostart_dir)
            if len(self.filename) > 0:
                self.load()

    def on_newConnection(self):
        # Active clientConnection
        self.clientConnection = self.server.nextPendingConnection()
        # Receive Data
        self.clientConnection.readyRead.connect(self.on_readyRead)
        # Disconnected
        self.clientConnection.disconnected.connect(self.on_disConnect)

        logger.info(self.tr('New TCP Client Connected'))

        if g.config.vars.Camera.camera_enable:
            if len(g.config.vars.Camera.camera_num) > 2:
                # Local Camera Mode
                addr = g.config.vars.Camera.camera_num
            else:
                # RTSP Camera Mode
                addr = int(g.config.vars.Camera.camera_num)
            # Init Camera
            self.cap = cv2.VideoCapture(addr, cv2.CAP_DSHOW)
            logger.info(self.tr('Camera Initialize Finish'))
        pass
    
    def on_disConnect(self):
        # If TCP Disconnected, Release Camera
        logger.info(self.tr('TCP Client Disconnected'))
        if hasattr(self,'cap'):
            self.cap.release()
            logger.info(self.tr('Camera Released'))

    def on_readyRead(self):
        # Incoming Data, Check with trigger word
        readData = self.clientConnection.readAll()
        readStr = str(readData, encoding='ascii')
        if readStr == g.config.vars.Trigger.tcp_server_letter:
            logger.info(self.tr('TCP Trigger Accepted'))
            # Got one frame and process
            self.startCameraShoot()
        pass

    def startCameraShoot(self):
        self.openCameraShoot()
        # FIXME Need add something return vars
        if hasattr(self.layerContents,'result'):
            sendData = str(self.layerContents.result).encode()
        else:
            sendData = 'Error'.encode()
        self.clientConnection.write(sendData)
        pass

    def tr(self, string_to_translate):
        """
        Translate a string using the QCoreApplication translation framework
        @param: string_to_translate: a unicode string
        @return: the translated unicode string if it was possible to translate
        """
        return str(QtCore.QCoreApplication.translate('MainWindow',
                                                           string_to_translate))

    def createActions(self):
        """
        Create the actions of the main toolbar.
        @purpose: Links the callbacks to the actions in the menu
        """

        # File
        self.ui.actionOpenFile.triggered.connect(self.open)
        self.ui.actionReload.triggered.connect(self.reload)
        self.ui.actionSaveProjectAs.triggered.connect(self.saveProject)
        self.ui.actionClose.triggered.connect(self.close)
        self.ui.actionOpenCamera.triggered.connect(self.openCamera)

        # Export
        self.ui.actionImageExport.triggered.connect(self.exportShapes)

        # Button
        self.ui.bOpenFile.clicked.connect(self.open)
        self.ui.bOpenCamera.clicked.connect(self.openCamera)
        self.ui.bAddLayout.clicked.connect(self.layerCreate)
        self.ui.bExport.clicked.connect(self.exportShapes)

        # Layout
        self.ui.layerCreatePushButton.clicked.connect(self.layerCreate)
        self.ui.layerDeletePushButton.clicked.connect(self.layerDelete)

        # View
        self.ui.actionAutoscale.triggered.connect(self.canvas.autoscale)

        # Options
        self.ui.actionConfiguration.triggered.connect(self.config_window.show)

        # Help
        self.ui.actionAbout.triggered.connect(self.about)

    def connectToolbarToConfig(self, project=False, block_signals=True):
        pass

    def keyPressEvent(self, event):
        """
        Rewritten KeyPressEvent to get other behavior while Shift is pressed.
        @purpose: Changes to ScrollHandDrag while Control pressed
        @param event:    Event Parameters passed to function
        """
        if event.isAutoRepeat():
            return
        if event.key() == QtCore.Qt.Key_Control:
            # Stop Camera Flow Mode
            self.cameraEnable = not self.cameraEnable
        elif event.key() == QtCore.Qt.Key_Shift:
            self.canvas.setDragMode(QGraphicsView.ScrollHandDrag)

    def keyReleaseEvent(self, event):
        """
        Rewritten KeyReleaseEvent to get other behavior while Shift is pressed.
        @purpose: Changes to RubberBandDrag while Control released
        @param event:    Event Parameters passed to function
        """
        if event.key() == QtCore.Qt.Key_Control:
            pass
        elif event.key() == QtCore.Qt.Key_Shift:
            self.canvas.setDragMode(QGraphicsView.NoDrag)

    def enableToolbarButtons(self, status=True):
        # File
        self.ui.actionReload.setEnabled(status)
        self.ui.actionSaveProjectAs.setEnabled(status)

        # Export
        self.ui.actionImageExport.setEnabled(status)

        # View
        self.ui.actionAutoscale.setEnabled(status)

        # Button
        self.ui.bAddLayout.setEnabled(status)
        self.ui.bExport.setEnabled(status)

    def exportShapes(self, status=False, saveas=None):
        if hasattr(self,'imglist'):
            imageWrite = self.imglist[len(self.imglist)-1]
            filename = self.showSaveDialog(self.tr('Export to file'), '*.jpg')[0]
            if len(filename) > 0:
                try:
                    cv2.imwrite(filename,imageWrite)
                    logger.info(self.tr("Export to FILE was successful"))
                except Exception as e:
                    logger.error(self.tr('Error with %s') % str (e))
                    QMessageBox.warning(g.window,
                                        self.tr("Error"),
                                        self.tr("Error with:\n%s") % str (e))

    def showSaveDialog(self, title, MyFormats):
        """
        This function is called by the menu "Export/Export Shapes" of the main toolbar.
        It creates the selection dialog for the exporter
        @return: Returns the filename of the selected file.
        """

        (beg, ende) = os.path.split(self.filename)
        (fileBaseName, fileExtension) = os.path.splitext(ende)

        default_name = os.path.join(os.path.dirname(self.filename), fileBaseName)
        #default_name = os.path.join(g.config.vars.Paths['output_dir'], fileBaseName)

        selected_filter = "*.jpg"
        filename = getSaveFileName(self,
                                   title, default_name,
                                   MyFormats, selected_filter)
        if len(filename[0]) > 0:
            logger.info(self.tr("File: %s selected") % filename[0])
            logger.info("<a href='%s'>%s</a>" % (filename[0], filename[0]))
        else:
            logger.info(self.tr("File Select Canceled"))
        return filename

    def about(self):
        """
        This function is called by the menu "Help/About" of the main toolbar and
        creates the About Window
        """

        message = self.tr("<html>"
                          "<h2><center>You are using</center></h2>"
                          "<body bgcolor="
                          "<center><h2>PY2CV - Python Opencv Industrial Vision</h2></center></body>"
                          "<h2>Version:</h2>"
                          "<body>%s: %s<br>"
                          "Last change: %s<br>"
                          "Changed by: %s<br></body>"
                          "<h2>Where to get help:</h2>"
                          "For more information and updates, "
                          "please visit "
                          "<a href='https://github.com/feecat/PY2CV'>https://github.com/feecat/PY2CV</a><br>"
                          "<h2>License and copyright:</h2>"
                          "<body>This program is written in Python and is published under the "
                          "<a href='http://www.gnu.org/licenses/'>GNU GPLv3 license.</a><br>"
                          "</body></html>") % (c.VERSION, c.REVISION, c.DATE, c.AUTHOR)

        AboutDialog(title=self.tr("About PY2CV"), message=message)

    def setMeasurementUnits(self, metric, refresh_ui=False):
        """
        Change the measurement units used in DXF file.
        Helps if py2cv was unable to detect the correct units.
        """

        if (g.config.metric != metric) or refresh_ui:
            logger.info(self.tr("Drawing units: Pixel"))

    def open(self):
        """
        This function is called by the menu "File/Load File" of the main toolbar.
        It creates the file selection dialog and calls the load function to
        load the selected file.
        """

        self.OpenFileDialog(self.tr("Open file"))

        # If there is something to load then call the load function callback
        if self.filename:
            self.cont_dx = 0.0
            self.cont_dy = 0.0
            self.cont_rotate = 0.0
            self.cont_scale = 1.0

            self.load()

    def OpenFileDialog(self, title):
        if len(self.filename) > 0:
            paths = os.path.dirname(self.filename)
        else:
            paths = g.config.vars.Paths['import_dir']
        self.filename, _ = getOpenFileName(self,
                                           title,
                                           paths,
                                           self.tr("All supported files (*.jpg *.jpeg *.jpe *.jfif *.bmp *.dib *.png *%s);;"
                                                   "Project files (*%s);;"
                                                   "JPEG files(*.jpg *.jpeg *.jpe *.jfif);;"
                                                   "BMP files(*.bmp *.dib);;"
                                                   "PNG files(*.png);;"
                                                   "All types (*.*)") % (c.PROJECT_EXTENSION, c.PROJECT_EXTENSION))

        # If there is something to load then call the load function callback
        if self.filename:
            self.filename = qstr_encode(self.filename)
            logger.info(self.tr("File: %s selected") % self.filename)

    def openCamera(self):
        self.cameraEnable = True
        QMessageBox.warning(g.window,
                    self.tr("Warning"),
                    self.tr("Will enter the streaming mode, press the CTRL key to exit."))
        if g.config.vars.Camera.camera_enable:
            if len(g.config.vars.Camera.camera_num) > 2:
                addr = g.config.vars.Camera.camera_num
            else:
                addr = int(g.config.vars.Camera.camera_num)
            if hasattr(self,'cap'):
                self.cap.release()
            self.cap = cv2.VideoCapture(addr, cv2.CAP_DSHOW)
            while True:
                if self.cameraEnable:
                    #schdule.enter(0.1,1,self.openCameraContinueMode1,())
                    #schdule.run()
                    try:
                        self.openCameraShoot()
                    except Exception as e:
                        logger.error(self.tr('Error with %s') % str (e))
                        QMessageBox.warning(g.window,
                                            self.tr("Error"),
                                            self.tr("Error with:\n%s") % str (e))
                        self.cap.release()
                        return
                    time.sleep(0.05)
                else:
                    self.cap.release()
                    return

    def openCameraShoot(self):
        ret, frame = self.cap.read()
        # FIXME if only one cap.read() it just got the LAST frame, not actual frame. this can be test in tcp trigger mode.
        ret, frame = self.cap.read()
        if ret == False:
            raise AssertionError("None frame capture")
        self.setWindowTitle("PY2CV - [%s]" % self.filename)
        self.canvas.resetAll()
        logger.info(self.tr('Loading Video Frame'))
        self.img = frame
        self.imglist = []
        self.imglist.append(self.img)
        self.imgshow()
        if len(self.layerContents) > 0:
            self.TreeHandler.buildEntitiesTree(self.layerContents)
            self.updateOpencv()
        self.app.processEvents()

    def load(self, plot=True):
        """
        Loads the file given by self.filename.  Also calls the command to
        make the plot.
        @param plot: if it should plot
        """
        if not QtCore.QFile.exists(self.filename):
            logger.info(self.tr("Cannot locate file: %s") % self.filename)
            self.OpenFileDialog(self.tr("Manually open file: %s") % self.filename)
            if not self.filename:
                return False  # cancelled

        self.setCursor(QtCore.Qt.WaitCursor)
        self.setWindowTitle("PY2CV - [%s]" % self.filename)
        self.canvas.resetAll()
        self.app.processEvents()

        (name, ext) = os.path.splitext(self.filename)

        if ext.lower() == c.PROJECT_EXTENSION:
            self.loadProject(self.filename)
            return True  # kill this load operation - we opened a new one

        logger.info(self.tr('Loading file: %s') % self.filename)

        self.img = cv2.imread(self.filename)
        self.imglist = []
        self.imglist.append(self.img)
        if plot:
            self.imgshow()
        
        if len(self.layerContents) > 0:
            self.TreeHandler.buildEntitiesTree(self.layerContents)
            self.updateOpencv()
        return True
    
    def imgshow(self):
        # Populate the treeViews
        #self.TreeHandler.buildEntitiesTree(self.entityRoot)

        # Paint the canvas
        self.canvas_scene = MyGraphicsScene()
        self.canvas.setScene(self.canvas_scene)
        # show image
        self.canvas_scene.plotAll(self)
        self.canvas.show()
        self.canvas.setFocus()
        self.canvas.autoscale()

        # After all is plotted enable the Menu entities
        self.enableToolbarButtons()
        self.unsetCursor()
    
    def updateOpencv(self):
        #clean first
        if hasattr(self,'img'):
            self.imglist.clear()
            self.imglist.append(self.img)
            if len(self.layerContents) > 0 and hasattr(self,'img'):
                for layerContent in self.layerContents:
                    if layerContent.enable > 0:
                        try:
                            if layerContent.name == 'Canny':
                                self.imglist.append(cv2.Canny(self.imglist[len(self.imglist)-1], layerContent.children[0].value, layerContent.children[1].value))
                            if layerContent.name == 'cvtColor':
                                self.imglist.append(cv2.cvtColor(self.imglist[len(self.imglist)-1], cv2.COLOR_RGB2GRAY))
                            if layerContent.name == 'threshold':
                                if layerContent.children[2] == 1:
                                    ret, th = cv2.threshold(self.imglist[len(self.imglist)-1],layerContent.children[0].value, layerContent.children[1].value, cv2.THRESH_BINARY + cv2.THRESH_TRIANGLE)
                                else:
                                    ret, th = cv2.threshold(self.imglist[len(self.imglist)-1],layerContent.children[0].value, layerContent.children[1].value, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                                self.imglist.append(th)
                            if layerContent.name == 'GaussianBlur':
                                self.imglist.append(cv2.GaussianBlur(self.imglist[len(self.imglist)-1],(layerContent.children[0].value, layerContent.children[1].value),layerContent.children[2].value))
                            if layerContent.name == 'findContours':
                                contours, hierarchy = cv2.findContours(self.imglist[len(self.imglist)-1], cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
                                self.imglist.append(cv2.drawContours(self.imglist[0].copy(),contours,-1, (255, 0, 255), 2))
                                self.imglist[0] = self.img
                            if layerContent.name == 'HoughLines':
                                lines = []
                                lines.clear()
                                lines = cv2.HoughLines(self.imglist[len(self.imglist)-1], layerContent.children[0].value, layerContent.children[1].value, layerContent.children[2].value)
                                if hasattr(lines,'size'):
                                    self.imglist.append(self.imglist[0].copy())
                                    self.imglist[0] = self.img
                                    for line in lines:
                                        rho, theta = line[0]
                                        a = np.cos(theta)
                                        b = np.sin(theta)
                                        x0 = a*rho
                                        y0 = b*rho
                                        x1 = int(x0 + 1000*(-b))
                                        y1 = int(y0 + 1000*(a))
                                        x2 = int(x0 - 1000*(-b))
                                        y2 = int(y0 - 1000*(a))
                                        cv2.line(self.imglist[len(self.imglist)-1],(x1,y1),(x2,y2),(0,0,255),2 , lineType=cv2.LINE_AA)
                                    self.layerContents.result = lines
                            if layerContent.name == 'HoughLinesP':
                                lines = []
                                lines.clear()
                                lines = cv2.HoughLinesP(self.imglist[len(self.imglist)-1], layerContent.children[0].value, layerContent.children[1].value, layerContent.children[2].value, minLineLength = layerContent.children[3].value, maxLineGap = layerContent.children[4].value)
                                if hasattr(lines,'size'):
                                    self.imglist.append(self.imglist[0].copy())
                                    self.imglist[0] = self.img
                                    for line in lines:
                                        x1, y1, x2, y2 = line[0]
                                        cv2.line(self.imglist[len(self.imglist)-1], (x1, y1), (x2, y2), (0, 255, 0), 1, lineType=cv2.LINE_AA)
                                    self.layerContents.result = lines
                            if layerContent.name == 'HoughCircles':
                                circles = []
                                circles.clear()
                                circles = cv2.HoughCircles(self.imglist[len(self.imglist)-1], cv2.HOUGH_GRADIENT, layerContent.children[0].value, layerContent.children[1].value, param1 = layerContent.children[2].value, param2 = layerContent.children[3].value, minRadius = int(layerContent.children[4].value), maxRadius = int(layerContent.children[5].value))
                                if hasattr(circles,'size'):
                                    self.imglist.append(self.imglist[0].copy())
                                    self.imglist[0] = self.img
                                    for i in circles[0, :]:
                                        cv2.circle(self.imglist[len(self.imglist)-1], (i[0], i[1]), int(i[2]), (0, 255, 0), 2)
                                        cv2.circle(self.imglist[len(self.imglist)-1], (i[0], i[1]), 2, (0, 0, 255), 3)
                                    self.layerContents.result = circles
                        except Exception as e:
                            logger.error(self.tr('Error with %s') % str (e))
                            QMessageBox.warning(g.window,
                                                self.tr("Error"),
                                                self.tr("Error with:\n%s") % str (e))

            self.canvas_scene.plotAll(self)
            pass
    
    def layerCreate(self):
        
        """
        This function is called when the Option=>Move WP Zero Menu is clicked.
        """
        title = self.tr('Create CV2 Layer')
        #label = [self.tr("Offset %s axis :") % (g.config.vars.Axis_letters['ax1_letter']),
        #         self.tr("Offset %s axis :") % (g.config.vars.Axis_letters['ax2_letter'])]
        #value = [self.cont_dx, self.cont_dy]
        label = [self.tr("Canny"),
                 self.tr("GaussianBlur"),
                 self.tr("cvtColor"),
                 self.tr("findContours"),
                 self.tr("HoughLines"),
                 self.tr("HoughLinesP"),
                 self.tr("HoughCircles"),
                 self.tr("threshold"),
                 ]
        abc = 0
        value = [abc]

        layerCreateDialog = PopUpDialog(title, label, value, True)

        if layerCreateDialog.result is None:
            return

        if self.entityRoot == None:
            self.entityRoot = []

        if layerCreateDialog.result == 'Canny':
            self.createCannyLayer()
        elif layerCreateDialog.result == 'GaussianBlur':
            self.createGaussianBlurLayer()
        elif layerCreateDialog.result == 'cvtColor':
            self.createcvtColorLayer()
        elif layerCreateDialog.result == 'findContours':
            self.createfindContoursLayer()
        elif layerCreateDialog.result == 'HoughLines':
            self.createHoughLinesLayer()
        elif layerCreateDialog.result == 'HoughLinesP':
            self.createHoughLinesPLayer()
        elif layerCreateDialog.result == 'HoughCircles':
            self.createHoughCirclesLayer()
        elif layerCreateDialog.result == 'threshold':
            self.createthresholdLayer()
        
        self.updateOpencv()
    
    def createcvtColorLayer(self):
            layerContent = Layers([])
            layerContent.name = 'cvtColor'
            layerContent.children=[]

            tempChildren = Layers([])
            tempChildren.name = 'low'
            tempChildren.value = 50
            tempChildren.note = 'threshold1'
            layerContent.children.append(tempChildren)

            self.layerContents.append(layerContent)
            self.TreeHandler.buildEntitiesTree(self.layerContents)

    def createCannyLayer(self):
            layerContent = Layers([])
            layerContent.name = 'Canny'
            layerContent.children=[]

            tempChildren = Layers([])
            tempChildren.name = 'low'
            tempChildren.value = 50
            tempChildren.note = 'threshold1'
            layerContent.children.append(tempChildren)

            tempChildren = Layers([])
            tempChildren.name = 'high'
            tempChildren.value = 100
            tempChildren.note = 'threshold2'
            layerContent.children.append(tempChildren)

            self.layerContents.append(layerContent)
            self.TreeHandler.buildEntitiesTree(self.layerContents)
    
    def createGaussianBlurLayer(self):
            layerContent = Layers([])
            layerContent.name = 'GaussianBlur'
            layerContent.children=[]

            tempChildren = Layers([])
            tempChildren.name = 'width'
            tempChildren.value = 3
            tempChildren.note = 'ksize.width'
            layerContent.children.append(tempChildren)

            
            tempChildren = Layers([])
            tempChildren.name = 'height'
            tempChildren.value = 3
            tempChildren.note = 'ksize.height'
            layerContent.children.append(tempChildren)

            tempChildren = Layers([])
            tempChildren.name = 'sigmaX'
            tempChildren.value = 0
            tempChildren.note = 'sigmaX'
            layerContent.children.append(tempChildren)

            tempChildren = Layers([])
            tempChildren.name = 'sigmaY'
            tempChildren.value = 0
            tempChildren.note = 'sigmaY'
            layerContent.children.append(tempChildren)

            self.layerContents.append(layerContent)
            self.TreeHandler.buildEntitiesTree(self.layerContents)

    def createfindContoursLayer(self):
        layerContent = Layers([])
        layerContent.name = 'findContours'
        layerContent.children=[]

        tempChildren = Layers([])
        tempChildren.name = 'RM'
        tempChildren.value = cv2.RETR_TREE
        tempChildren.note = 'RetrievalModes'
        layerContent.children.append(tempChildren)

        tempChildren = Layers([])
        tempChildren.name = 'CAM'
        tempChildren.value = cv2.CHAIN_APPROX_SIMPLE
        tempChildren.note = 'ContourApproximationModes'
        layerContent.children.append(tempChildren)

        self.layerContents.append(layerContent)
        self.TreeHandler.buildEntitiesTree(self.layerContents)

    def createHoughLinesLayer(self):
        layerContent = Layers([])
        layerContent.name = 'HoughLines'
        layerContent.children=[]

        tempChildren = Layers([])
        tempChildren.name = 'rho'
        tempChildren.value = 0.8
        tempChildren.note = 'Distance resolution'
        layerContent.children.append(tempChildren)

        tempChildren = Layers([])
        tempChildren.name = 'theta'
        tempChildren.value = 0.01
        tempChildren.note = 'Angle resolution'
        layerContent.children.append(tempChildren)

        tempChildren = Layers([])
        tempChildren.name = 'threshold'
        tempChildren.value = 100
        tempChildren.note = 'Accumulator threshold parameter'
        layerContent.children.append(tempChildren)

        self.layerContents.append(layerContent)
        self.TreeHandler.buildEntitiesTree(self.layerContents)
    
    def createHoughLinesPLayer(self):
        layerContent = Layers([])
        layerContent.name = 'HoughLinesP'
        layerContent.children=[]
        tempChildren = Layers([])

        tempChildren.name = 'rho'
        tempChildren.value = 0.8
        tempChildren.note = 'Distance resolution'
        layerContent.children.append(deepcopy(tempChildren))
        
        tempChildren.name = 'theta'
        tempChildren.value = 0.01
        tempChildren.note = 'Angle resolution'
        layerContent.children.append(deepcopy(tempChildren))

        tempChildren.name = 'threshold'
        tempChildren.value = 100
        tempChildren.note = 'Accumulator threshold parameter'
        layerContent.children.append(deepcopy(tempChildren))

        tempChildren.name = 'minLineLength'
        tempChildren.value = 10
        tempChildren.note = 'Minimum line length'
        layerContent.children.append(deepcopy(tempChildren))

        tempChildren.name = 'maxLineGap'
        tempChildren.value = 500
        tempChildren.note = 'Maximum allowed gap'
        layerContent.children.append(deepcopy(tempChildren))

        self.layerContents.append(layerContent)
        self.TreeHandler.buildEntitiesTree(self.layerContents)

    def createthresholdLayer(self):
        layerContent = Layers([])
        layerContent.name = 'threshold'
        layerContent.children=[]
        tempChildren = Layers([])

        tempChildren.name = 'thresh'
        tempChildren.value = 0
        tempChildren.note = 'thresh'
        layerContent.children.append(deepcopy(tempChildren))

        tempChildren.name = 'maxval'
        tempChildren.value = 255
        tempChildren.note = 'maxval'
        layerContent.children.append(deepcopy(tempChildren))

        tempChildren.name = 'triangle'
        tempChildren.value = 0
        tempChildren.note = '0=otsu,1=triangle'
        layerContent.children.append(deepcopy(tempChildren))

        self.layerContents.append(layerContent)
        self.TreeHandler.buildEntitiesTree(self.layerContents)


    def createHoughCirclesLayer(self):
            layerContent = Layers([])
            layerContent.name = 'HoughCircles'
            layerContent.children=[]
            tempChildren = Layers([])

            tempChildren.name = 'dp'
            tempChildren.value = 1.5
            tempChildren.note = 'Inverse ratio'
            layerContent.children.append(deepcopy(tempChildren))

            tempChildren.name = 'minDist'
            tempChildren.value = 100
            tempChildren.note = 'Minimum distance between two circles'
            layerContent.children.append(deepcopy(tempChildren))

            tempChildren.name = 'param1'
            tempChildren.value = 100
            tempChildren.note = 'do not change'
            layerContent.children.append(deepcopy(tempChildren))

            tempChildren.name = 'param2'
            tempChildren.value = 30
            tempChildren.note = 'do not change'
            layerContent.children.append(deepcopy(tempChildren))

            tempChildren.name = 'minRadius'
            tempChildren.value = 10
            tempChildren.note = 'Minimum circle radius'
            layerContent.children.append(deepcopy(tempChildren))

            tempChildren.name = 'maxRadius'
            tempChildren.value = 0
            tempChildren.note = 'Maximum circle radius'
            layerContent.children.append(deepcopy(tempChildren))

            self.layerContents.append(layerContent)
            self.TreeHandler.buildEntitiesTree(self.layerContents)

    def layerDelete(self):
        if self.TreeHandler.ui.entitiesTreeView.selectionModel() != None:
            selectedRows = self.TreeHandler.ui.entitiesTreeView.selectionModel().selectedRows()
            if len(selectedRows) > 0:
                if selectedRows[0].parent().row() == -1:
                    # no parent
                    row = selectedRows[0].row()
                else:
                    # have parent
                    row = selectedRows[0].parent().row()
                self.layerContents.pop(row)
                self.TreeHandler.buildEntitiesTree(self.layerContents)
                logger.debug(self.tr("removed layer: %s" % str(row)))
                self.updateOpencv()
                return
        logger.debug(self.tr("nothing remove"))
    
    def layerMoveUp(self):
        pass

    def layerMoveDown(self):
        pass

    def reload(self):
        """
        This function is called by the menu "File/Reload File" of the main toolbar.
        It reloads the previously loaded file (if any)
        """
        if self.filename:
            logger.info(self.tr("Reloading file: %s") % self.filename)
            self.load()

    def updateConfiguration(self, result):
        """
        Some modification occured in the configuration window, we need to save these changes into the config file.
        Once done, the signal configuration_changed is emitted, so that anyone interested in this information can connect to this signal.
        """
        if result == ConfigWindow.Applied or result == ConfigWindow.Accepted:
            # Write the configuration into the config file (config.cfg)
            g.config.save_varspace()
            # Rebuild the readonly configuration structure
            g.config.update_config()

            # Assign changes to the menus (if no change occured, nothing
            # happens / otherwise QT emits a signal for the menu entry that has changed)
            self.connectToolbarToConfig(block_signals=False)

            # Inform about the changes into the configuration
            self.configuration_changed.emit()

    def loadProject(self, filename):
        """
        Load all variables from file
        """
        # since Py3 has no longer execfile -  we need to open it manually
        file_ = open(filename, 'r')
        str_ = file_.read()
        file_.close()
        self.d2g.load(str_)

    def saveProject(self):
        """
        Save all variables to file
        """
        prj_filename = self.showSaveDialog(self.tr('Save project to file'), "Project files (*%s)" % c.PROJECT_EXTENSION)
        save_prj_filename = qstr_encode(prj_filename[0])

        # If Cancel was pressed
        if not save_prj_filename:
            return

        (beg, ende) = os.path.split(save_prj_filename)
        (fileBaseName, fileExtension) = os.path.splitext(ende)

        if fileExtension != c.PROJECT_EXTENSION:
            if not QtCore.QFile.exists(save_prj_filename):
                save_prj_filename += c.PROJECT_EXTENSION

        pyCode = self.d2g.export()
        try:
            # File open and write
            f = open(save_prj_filename, "w")
            f.write(str_encode(pyCode))
            f.close()
            logger.info(self.tr("Save project to FILE was successful"))
        except IOError:
            QMessageBox.warning(g.window,
                                self.tr("Warning during Save Project As"),
                                self.tr("Cannot Save the File"))

    def closeEvent(self, e):
        logger.debug(self.tr("Closing"))
        self.saveWindowState()
        self.cameraEnable = False
        e.accept()

    def restoreWindowState(self):
        self.settings.beginGroup("MainWindow")
        geometry = self.settings.value("geometry")
        state = self.settings.value("state")
        self.settings.endGroup()
        if (geometry is not None) and (state is not None):
            self.restoreGeometry(geometry)
            self.restoreState(state)

    def saveWindowState(self):
        self.settings.beginGroup("MainWindow")
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("state", self.saveState())
        self.settings.endGroup()


if __name__ == "__main__":
    """
    The main function which is executed after program start.
    """
    Log = LoggerClass(logger)

    g.config = MyConfig()
    Log.set_console_handler_loglevel()

    if not g.config.vars.Logging['logfile']:
        Log.add_window_logger()
    else:
        Log.add_file_logger()

    app = QApplication(sys.argv)

    # Get local language and install if available.
    locale = QtCore.QLocale.system().name()
    logger.debug("locale: %s" % locale)
    translator = QtCore.QTranslator()
    if translator.load("py2cv_" + locale, "./locales"):
        app.installTranslator(translator)

    # If string version_mismatch isn't empty, we popup an error and exit
    if g.config.version_mismatch:
        error_message = QMessageBox(QMessageBox.Critical, 'Configuration error', g.config.version_mismatch)
        sys.exit(error_message.exec_())

    # Delay imports - needs to be done after logger and config initialization; and before the main window
    from py2cv_ui5 import Ui_MainWindow

    from py2cv.gui.canvas2d import MyGraphicsScene
    from py2cv.gui.canvas2d import ShapeGUI as Shape
    window = MainWindow(app)
    g.window = window
    Log.add_window_logger(window.ui.messageBox)


    # command line options
    parser = argparse.ArgumentParser()

    parser.add_argument("filename", nargs="?")

#    parser.add_argument("-f", "--file", dest = "filename",
#                        help = "read data from FILENAME")
    parser.add_argument("-e", "--export", dest="export_filename",
                        help="export data to FILENAME")
    parser.add_argument("-q", "--quiet", action="store_true",
                        dest="quiet", help="no GUI")
#    parser.add_option("-v", "--verbose",
#                      action = "store_true", dest = "verbose")
    options = parser.parse_args()
    g.quiet = options.quiet

    # (options, args) = parser.parse_args()
    logger.debug("Started with following options:\n%s" % parser)

    if not options.quiet:
        window.show()

    if options.filename is not None:
        window.filename = str_decode(options.filename)
        window.load()

    if options.export_filename is not None:
        window.exportShapes(None, options.export_filename)

    if not options.quiet:
        # It's exec_ because exec is a reserved word in Python
        sys.exit(app.exec_())
