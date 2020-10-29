# -*- coding: utf-8 -*-

############################################################################
#
#   Copyright (C) 2015
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
import hashlib
import re

from copy import deepcopy
from py2cv.core.customgcode import CustomGCode
from py2cv.core.layercontent import Layers, Shapes
from py2cv.globals.d2gexceptions import VersionMismatchError
import py2cv.globals.globals as g

import py2cv.globals.constants as c
from PyQt5 import QtCore

logger = logging.getLogger("Core.Project")

def execute(self, content):
    # hack to use exec with local variables, for sure; To prevent the following error
    # SyntaxError: unqualified exec is not allowed in function 'load' it contains a nested function with free variables
    # this error is a Python 2.7 compiler bug (http://bugs.python.org/issue21591) - might occur in the earlier versions
    exec(content, {'d2g': self})

class Project(object):
    header = "# +~+~+~ DXF2GCODE project file V%s ~+~+~+"
    supported_versions = [1.1, 1.2]
    version = supported_versions[-1]

    def __init__(self, parent):
        self.parent = parent

        self.file = None
        self.point_tol = None
        self.fitting_tol = None
        self.scale = None
        self.rot = None
        self.wpzero_x = None
        self.wpzero_y = None
        self.split_lines = None
        self.aut_cut_com = None
        self.machine_type = None

        self.layers = None

    def tr(self, string_to_translate):
        """
        Translate a string using the QCoreApplication translation framework
        @param: string_to_translate: a unicode string
        @return: the translated unicode string if it was possible to translate
        """
        return str(QtCore.QCoreApplication.translate('Project',
                                                           string_to_translate))

    def get_hash(self, shape, version):
        reverse = False
        if not shape.cw:
            reverse = True
            shape.reverse()

        shape_iter = shape.geos if version < 1.2 else shape.geos.abs_iter()  # new versions look at absolute values
        geos = [geo.save_v1() for geo in shape_iter]
        if reverse:
            shape.reverse()
        return hashlib.sha1(''.join(sorted(geos)).encode('utf-8')).hexdigest()

    def export(self):
        self.parent.TreeHandler.updateExportOrder(True)
        layers = []
        for layer in self.parent.layerContents:
            shapes = []
            for children in layer.children:
                shapes.append({'name':children.name,
                                      'value': children.value,
                                      'note': children.note})
            layers.append({'name': layer.name,
                           'shapes': shapes})

        pyCode = Project.header % str(Project.version) + '\n' +\
                'd2g.file = ' + '"' + self.parent.filename + '"' + '\n' +\
                'd2g.layers = ' + str(layers)
        return pyCode

    def load(self, content, compleet=True):
        match = re.match(Project.header.replace('+', '\+') % r'(\d+\.\d+)', content)
        if not match:
            raise Exception('Incorrect project file')
        version = float(match.groups()[0])
        if version not in  Project.supported_versions:
            raise VersionMismatchError(match.group(), Project.version)

        execute(self, content)

        if compleet:
            self.parent.filename = self.file

            self.parent.connectToolbarToConfig(True)
            if not self.parent.load(False):
                self.parent.unsetCursor()
                return

        layers = []
        layer = Layers([])
        for parent_layer in self.layers:
            layer.name = parent_layer['name']
            layer.children = []

            tempLayer = Layers([])
            for shape in parent_layer['shapes']:
                tempLayer.clear()
                tempLayer.name = shape['name']
                tempLayer.value = shape['value']
                tempLayer.note = shape['note']
                layer.children.append(deepcopy(tempLayer))
            
            layers.append(deepcopy(layer))

        self.parent.layerContents = Layers(layers)  # overwrite original
        self.parent.load()

    def reload(self, compleet=True):
        if self.parent.filename:
            self.parent.setCursor(QtCore.Qt.WaitCursor)
            self.parent.canvas.resetAll()
            self.parent.app.processEvents()
            pyCode = self.export()
            self.parent.makeShapes()
            self.load(pyCode, compleet)

    def small_reload(self):
        self.reload(False)
