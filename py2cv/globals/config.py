# -*- coding: utf-8 -*-

############################################################################
#
#   Copyright (C) 2009-2016
#    Christian Kohlöffel
#    Jean-Paul Schouwstra
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

from __future__ import absolute_import

import os
import sys
import pprint
import logging

from collections import OrderedDict
from configobj import ConfigObj, flatten_errors
from validate import Validator
import py2cv.globals.globals as g
from py2cv.globals.d2gexceptions import *
from py2cv.gui.configwindow import *

import py2cv.globals.constants as c
from PyQt5 import QtCore


logger = logging.getLogger("Core.Config")

CONFIG_VERSION = "9.10"
"""
version tag - increment this each time you edit CONFIG_SPEC

compared to version number in config file so
old versions are recognized and skipped"
"""

# Paths change whether platform is Linux or Windows
if "linux" in sys.platform.lower() or "unix" in sys.platform.lower():
    #Declare here the path that are specific to Linux
    IMPORT_DIR = "~/Documents"
    OUTPUT_DIR = "~/Documents"
else:
    #Declare here the path that are specific to Windows
    IMPORT_DIR = "D:"
    OUTPUT_DIR = "D:"

"""
HOWTO declare a new variable in the config file:
1) Choose the appropriate section and add the variable in the CONFIG_SPEC string below
(Note: the CONFIG_SPEC is used to set and check the configfile "config.cfg")

2) Set it's default value, the min/max values (if applicable) and a comment above the variable's name
(Important note: the min/max values and the comment are directly used in the configuration window, so carefully set them!)
Example of correct declaration:
    [MySection]
    # Drag angle is used to blah blah blah ...
    drag_angle = float(min = 0, max = 360, default = 20)

3) If you want the setting to appear in the configuration window, fill the cfg_widget_def variable, using the _same_ names as in the CONFIG_SPEC
Example of declaration correlated to the above one:
    'MySection':
    {
        'drag_angle': CfgDoubleSpinBox('Drag angle (in degrees):'),
    }
(Note: the list of available types for the configuration window can be found in the "configwindow.py" file)
"""
"""
ATTENTION:
_Don't_ split the long comments lines in CONFIG_SPEC!
The comments line are used as "QWhatsThis" in the config window.
Any new line in the CONFIG_SPEC is reproduced in the QWhatsThis (intented behaviour to allow creating paragraphs)
ATTENTION
"""
CONFIG_SPEC = str('''
#  Section and variable names must be valid Python identifiers
#      do not use whitespace in names

# do not edit the following section name:
    [Version]
    # do not edit the following value:
    config_version = string(default = "''' +
    str(CONFIG_VERSION) + '")\n' +
    '''
    [Paths]
    # By default look for DXF files in this directory.
    import_dir = string(default = "''' + IMPORT_DIR + '''")

    # Export generated gcode by default to this directory.
    output_dir = string(default = "''' + OUTPUT_DIR + '''")

    [Camera]
    camera_enable = boolean(default = True)
    camera_num = string(default = "0")

    [AutoStart]
    autostart_enable = boolean(default = False)
    autostart_dir = string(default = "''' + IMPORT_DIR + '''")

    [Trigger]
    tcp_server_enable = boolean(default = False)
    tcp_server_port = integer(min = 0, max = 65535, default = 8070)
    tcp_server_letter = string(default = "a")

    # Define here custom GCODE actions:
    # - name: this is the unique name of the action
    # - gcode: the text that will be inserted in the final program (each new line is also translated as a new line in the output file)
    # Custom actions can be inserted in the program by using right-click contextual menu on the treeview.
    [Custom_Actions]
    [[__many__]]
    gcode = string(default = "(change subsection name and insert your custom GCode here. Use triple quote to place the code on several lines)")

    [Logging]
    # Logging to textfile is disabled by default
    logfile = string(default = "")

    # This really goes to stderr
    console_loglevel = option('DEBUG', 'INFO', 'WARNING', 'ERROR','CRITICAL', default = 'CRITICAL')

    # Log levels are, in increasing importance: DEBUG; INFO; WARNING; ERROR; CRITICAL
    # Log events with importance >= loglevel are logged to the corresponding output
    file_loglevel = option('DEBUG', 'INFO', 'WARNING', 'ERROR','CRITICAL', default = 'DEBUG')

    # Logging level for the message window
    window_loglevel = option('DEBUG', 'INFO', 'WARNING', 'ERROR','CRITICAL', default = 'INFO')

''').splitlines()
""" format, type and default value specification of the global config file"""


class MyConfig(object):
    """
    This class hosts all functions related to the Config File.
    """
    def __init__(self):
        """
        initialize the varspace of an existing plugin instance
        init_varspace() is a superclass method of plugin
        """

        #self.folder = os.path.join(g.folder, c.DEFAULT_CONFIG_DIR)
        self.folder = g.folder
        self.filename = os.path.join(self.folder, 'config' + c.CONFIG_EXTENSION)

        self.version_mismatch = '' # no problem for now
        self.default_config = False # whether a new name was generated
        self.var_dict = dict()
        self.spec = ConfigObj(CONFIG_SPEC, interpolation=False, list_values=False, _inspec=True)

        # try:
        self.load_config()
        self.update_config()

        self.metric = 0   # Standard if no other unit is determined while importing
        self.tool_units = 1 # store the initial tool_units (we don't want it to change until software restart)
        self.tool_units_metric = 0

        # except Exception, msg:
        #     logger.warning(self.tr("Config loading failed: %s") % msg)
        #     return False

    def tr(self, string_to_translate):
        """
        Translate a string using the QCoreApplication translation framework
        @param string_to_translate: a unicode string
        @return: the translated unicode string if it was possible to translate
        """
        return str(QtCore.QCoreApplication.translate('MyConfig',
                                                           string_to_translate))

    def update_config(self):
        """
        Call this function each time the self.var_dict is updated (eg when the configuration window changes some settings)
        """
        # convenience - flatten nested config dict to access it via self.config.sectionname.varname
        self.vars = DictDotLookup(self.var_dict)
        # add here any update needed for the internal variables of this class

    def make_settings_folder(self):
        """Create settings folder if necessary"""
        try:
            os.makedirs(self.folder)
        except OSError:
            pass

    def load_config(self):
        """Load Config File"""
        
        logger.info(self.filename)
        
        if os.path.isfile(self.filename):
            try:
                # file exists, read & validate it
                self.var_dict = ConfigObj(self.filename, configspec=CONFIG_SPEC)
                _vdt = Validator()
                result = self.var_dict.validate(_vdt, preserve_errors=True)
                validate_errors = flatten_errors(self.var_dict, result)

                if validate_errors:
                    logger.error(self.tr("errors reading %s:") % self.filename)

                for entry in validate_errors:
                    section_list, key, error = entry
                    if key is not None:
                        section_list.append(key)
                    else:
                        section_list.append('[missing section]')
                    section_string = ', '.join(section_list)
                    if not error:
                        error = self.tr('Missing value or section.')
                    logger.error(section_string + ' = ' + error)

                if validate_errors:
                    raise BadConfigFileError("syntax errors in config file")

                # check config file version against internal version
                if CONFIG_VERSION:
                    fileversion = self.var_dict['Version']['config_version']  # this could raise KeyError

                    if fileversion != CONFIG_VERSION:
                        raise VersionMismatchError(fileversion, CONFIG_VERSION)

            except VersionMismatchError:
                #raise VersionMismatchError(fileversion, CONFIG_VERSION)
                # version mismatch flag, it will be used to display an error.
                self.version_mismatch = self.tr("The configuration file version ({0}) doesn't match the software expected version ({1}).\n\nYou have to delete (or carefully edit) the configuration file \"{2}\" to solve the problem.").format(fileversion, CONFIG_VERSION, self.filename)

            except Exception as inst:
                logger.error(inst)
                (base, ext) = os.path.splitext(self.filename)
                badfilename = base + c.BAD_CONFIG_EXTENSION
                logger.debug(self.tr("trying to rename bad cfg %s to %s") % (self.filename, badfilename))
                try:
                    os.replace(self.filename, badfilename)
                except OSError as e:
                    logger.error(self.tr("rename(%s,%s) failed: %s") % (self.filename, badfilename, e.strerror))
                    raise
                else:
                    logger.debug(self.tr("renamed bad varspace %s to '%s'") % (self.filename, badfilename))
                    self.create_default_config()
                    self.default_config = True
                    logger.debug(self.tr("created default varspace '%s'") % self.filename)
            else:
                self.default_config = False
                # logger.debug(self.dir())
                # logger.debug(self.tr("created default varspace '%s'") % self.filename)
                # logger.debug(self.tr("read existing varspace '%s'") % self.filename)
        else:
            self.create_default_config()
            self.default_config = True
            logger.debug(self.tr("created default varspace '%s'") % self.filename)

        self.var_dict.main.interpolation = False  # avoid ConfigObj getting too clever

    def create_default_config(self):
        # check for existing setting folder or create one
        self.make_settings_folder()

        # derive config file with defaults from spec
        self.var_dict = ConfigObj(configspec=CONFIG_SPEC)
        _vdt = Validator()
        self.var_dict.validate(_vdt, copy=True)
        self.var_dict.filename = self.filename
        self.var_dict.write()

    def save_varspace(self):
        """Saves Variables space"""
        self.var_dict.filename = self.filename
        self.var_dict.write()

    def print_vars(self):
        """Prints Variables"""
        print("Variables:")
        for k, v in self.var_dict['Variables'].items():
            print(k, "=", v)

    def makeConfigWidgets(self):
        """
        Build the configuration widgets and store them into a dictionary.
        The structure of the dictionnary must match the structure of the configuration file. The names of the keys must be identical to those used in the configfile.
        If a name is declared in the configfile but not here, it simply won't appear in the config window (the config_version for example must not be modified by the user, so it is not declared here)
        """
        coordinate_unit = self.tr(" mm") if self.tool_units_metric else self.tr(" in")
        speed_unit = self.tr(" mm/min") if self.tool_units_metric else self.tr(" IPS")
        cfg_widget_def = OrderedDict([
            ('__section_title__', {
                # This section is only used for assigning titles to the keys of the dictionnary (= name of the sections used in the config file).
                # This name is displayed in the tabs of the configuration window ; if no name is provided, the key name is used. A same title may be used for several keys : in this case, all the items that belongs to this section are regrouped into the same tab.
                # Note: the title may be specified in the section itselt too, using special entry "'__section_title__': Title to use"
                'Tool_Parameters': self.tr("Tools table"),
                'Custom_Actions' : self.tr("Custom actions")}),
            ('Paths', OrderedDict([
                ('__section_title__', self.tr("Software config")),
                ('__subtitle__', CfgSubtitle("Directory")),
                ('import_dir', CfgLineEdit(self.tr('By default look for files in:'))),
            ])),
            ('Camera', OrderedDict([
                ('__section_title__', self.tr("Software config")),
                ('__subtitle__', CfgSubtitle("Camera")),
                ('camera_enable', CfgCheckBox(self.tr('Camera Enable'))),
                ('camera_num', CfgLineEdit(self.tr('Camera Number: (Also Support RTSP Camera)'))),
            ])),
            ('AutoStart', OrderedDict([
                ('__section_title__', self.tr("Software config")),
                ('__subtitle__', CfgSubtitle("Auto Start")),
                ('autostart_enable', CfgCheckBox(self.tr('Auto Start Enable (Will Auto Start Camera and TCP Server when software start)'))),
                ('autostart_dir', CfgLineEdit(self.tr('By default look for files at:'))),
            ])),
            ('Trigger', OrderedDict([
                ('__section_title__', self.tr("Software config")),
                ('__subtitle__', CfgSubtitle("Trigger Host (TCP)")),
                ('tcp_server_enable', CfgCheckBox(self.tr('Enable TCP Server'))),
                ('tcp_server_port', CfgLineEdit(self.tr('Host Port:'))),
                ('tcp_server_letter', CfgLineEdit(self.tr('Host Letter:'))),
            ])),
            ('Custom_Actions', CfgTableCustomActions(self.tr('Define here custom GCODE that can be inserted anywhere in the program:'))),
            ('Logging', OrderedDict([
                ('__section_title__', self.tr("Software config")),
                ('__subtitle__', CfgSubtitle("Logger")),
                ('logfile', CfgLineEdit(self.tr('File used for logging (restart needed):'))),
                ('console_loglevel', CfgComboBox(self.tr('On stderr console log messages with importance minimal to level (restart needed):'))),
                ('file_loglevel', CfgComboBox(self.tr('For log-file log messages with importance minimal to level (restart needed):'))),
                ('window_loglevel', CfgComboBox(self.tr('For message box log messages with importance minimal to level (restart needed):'))),
            ]))
        ])

        return cfg_widget_def

    def update_tool_values(self):
        """
        update the tool default values depending on the unit of the drawing
        """
        if self.tool_units_metric != self.metric:
            scale = 1/25.4 if self.metric == 0 else 25.4
            for key in self.vars.Plane_Coordinates:
                self.vars.Plane_Coordinates[key] *= scale
            for key in self.vars.Depth_Coordinates:
                self.vars.Depth_Coordinates[key] *= scale
            for key in self.vars.Feed_Rates:
                self.vars.Feed_Rates[key] *= scale
            for tool in self.vars.Tool_Parameters:
                self.vars.Tool_Parameters[tool]['diameter'] *= scale
                self.vars.Tool_Parameters[tool]['start_radius'] *= scale
            self.tool_units_metric = self.metric


class DictDotLookup(object):
    """
    Creates objects that behave much like a dictionaries, but allow nested
    key access using object '.' (dot) lookups.
    """
    def __init__(self, d):
        for k in d:
            if isinstance(d[k], dict):
                self.__dict__[k] = DictDotLookup(d[k])
            elif isinstance(d[k], (list, tuple)):
                l = []
                for v in d[k]:
                    if isinstance(v, dict):
                        l.append(DictDotLookup(v))
                    else:
                        l.append(v)
                self.__dict__[k] = l
            else:
                self.__dict__[k] = d[k]

    def __getitem__(self, name):
        if name in self.__dict__:
            return self.__dict__[name]

    def __setitem__(self, name, value):
        if name in self.__dict__:
            self.__dict__[name] = value

    def __iter__(self):
        return iter(self.__dict__.keys())

    def __repr__(self):
        return pprint.pformat(self.__dict__)

# if __name__ == '__main__':
#     cfg_data = eval("""{
#         'foo' : {
#             'bar' : {
#                 'tdata' : (
#                     {'baz' : 1 },
#                     {'baz' : 2 },
#                     {'baz' : 3 },
#                 ),
#             },
#         },
#         'quux' : False,
#     }""")
#
#     cfg = DictDotLookup(cfg_data)
#
#     # iterate
#     for k, v in cfg.__iter__(): #foo.bar.iteritems():
#         print k, " = ", v
#
#     print "cfg=", cfg
#
#     #   Standard nested dictionary lookup.
#     print 'normal lookup :', cfg['foo']['bar']['tdata'][0]['baz']
#
#     #   Dot-style nested lookup.
#     print 'dot lookup    :', cfg.foo.bar.tdata[0].baz
#
#     print "qux=", cfg.quux
#     cfg.quux = '123'
#     print "qux=", cfg.quux
#
#     del cfg.foo.bar
#     cfg.foo.bar = 4711
#     print 'dot lookup    :', cfg.foo.bar #.tdata[0].baz
