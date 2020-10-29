# -*- coding: utf-8 -*-

############################################################################
#
#   Copyright (C) 2015-2016
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
@purpose: build a configuration window on top of ConfigObj configfile module.

It aims to be generic and reusable for many configuration windows.

*** Basic usage ***
1) Let's say that your ConfigObj spec file is declared as is:
CONFIG_SPEC = str('''
    [MySection]
    # Comment for the variable below
    my_variable = float(min = 0, max = 360, default = 20)
    ''').splitlines()

2) Declare the corresponding dictionnary
config_widget_dict = OrderedDict([
        ('MySection', OrderedDict([
            ('__section_title__', "My Title"),
            ('__subtitle__', CfgSubtitle(self.tr("My possible subtitle"))),
            ('my_variable', CfgDoubleSpinBox("My parameter description")),
            ('my_variable2', CfgDoubleSpinBox("My parameter description2")),
            ('NextSubtitleX', CfgSubtitle(self.tr("My not needed second subtitle"))),
            ('my_variable3', CfgDoubleSpinBox("My parameter description3"))
        ])),
    ])

The my __subtitle__ is not restricted to be placed under __section_title__ it can be placed on any line and
it is also not restricted to be named like that. You can even leave it out. If you do it's replaced by a line.
If you place it on a different line (with the name:__subtitle__), this subsection does not start with horizontal bar.

3) Instanciate the config window:
config_window = ConfigWindow(config_widget_dict, var_dict, configspec, self) #See ConfigObj for var_dict & configspec
config_window.finished.connect(self.updateConfiguration) #Optional signal to know when the config has changed

*** List of graphical elements currently supported ***
 - CfgSubtitle(): subtitle - just for displaying a bar with some text
 - CfgCheckBox(): a basic (possibly tristate) checkbox
 - CfgSpinBox(): a spinbox for int values
 - CfgDoubleSpinBox(): a spinbox for float values
 - CfgLineEdit(): a text input (1 line)
 - CfgListEdit(): a text list input (1 line)
 - CfgTextEdit(): a text input (multiple lines)
 - CfgComboBox(): a drop-down menu for selecting options
 - CfgTable(): a 2D table with editable text entries
 - CfgTableCustomActions(): specific module based on CfgTable(), for storing custom GCODE
 - CfgTableToolParameters(): specific module based on CfgTable(), for storing mill tools
"""

from __future__ import absolute_import

import logging
from collections import OrderedDict

from py2cv.globals.helperfunctions import toInt, toFloat, str_encode, qstr_encode

import py2cv.globals.constants as c

from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QMessageBox, QVBoxLayout, QHBoxLayout, QLayout, QFrame, \
    QLabel, QLineEdit, QTextEdit, QCheckBox, QSpinBox, QDoubleSpinBox, QComboBox, QTableWidget, QTableWidgetItem, \
    QPushButton, QAbstractItemView, QWidget, QSizePolicy, QListWidget, QStackedWidget, QSplitter
from PyQt5.QtGui import QIcon, QPixmap, QValidator, QRegExpValidator
from PyQt5.QtCore import QLocale, QRegExp
from PyQt5 import QtCore

from py2cv.gui.popupdialog import PopUpDialog

logger = logging.getLogger("Gui.ConfigWindow")


class ConfigWindow(QDialog):
    Applied = QDialog.Accepted + QDialog.Rejected + 1 #Define a result code that is different from accepted and rejected

    """Main Class"""
    def __init__(self, definition_dict, config = None, configspec = None, parent = None, title = "Configuration"):
        """
        Initialization of the Configuration window. ConfigObj must be instanciated before this one.
        @param definition_dict: the dict that describes our window
        @param config: data readed from the configfile. This dict is created by ConfigObj module.
        @param configspec: specifications of the configfile. This variable is created by ConfigObj module.
        """
        QDialog.__init__(self, parent)
        self.setWindowTitle(title)
        iconWT = QIcon()
        iconWT.addPixmap(QPixmap(":images/opencv.ico"), QIcon.Normal, QIcon.Off)
        self.setWindowIcon(QIcon(iconWT))

        self.edition_mode = False #No editing in progress for now

        self.cfg_window_def = definition_dict #This is the dict that describes our window
        self.var_dict = config #This is the data from the configfile (dictionary created by ConfigObj class)
        self.configspec = configspec #This is the specifications for all the entries defined in the config file

        #There is no config file selector for now, so no callback either
        self.selector_change_callback = None
        self.selector_add_callback = None
        self.selector_remove_callback = None
        self.selector_duplicate_callback = None

        #Create the vars for the optional configuration's file selector
        self.cfg_file_selector = None
        self.frame_file_selector = CfgBase() #For displaying the optionnal files selector widgets

        #Create the config window according to the description dict received
        self.list_items = self.createWidgetFromDefinitionDict()

        #Create 3 buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Discard | QDialogButtonBox.Apply | QDialogButtonBox.Close)
        self.button_box.accepted.connect(self.accept) #Apply and close (currently unused)
        self.button_box.rejected.connect(self.reject) #Close
        apply_button = self.button_box.button(QDialogButtonBox.Apply)
        apply_button.clicked.connect(self.applyChanges) #Apply button
        discard_button = self.button_box.button(QDialogButtonBox.Discard)
        discard_button.clicked.connect(self.discardChanges) #Discard button

        #Layout
        list_widget = QListWidget(parent)
        self.tab_window = QStackedWidget()
        for label, widget in self.list_items.items():
            list_widget.addItem(label)
            self.tab_window.addWidget(widget)

        list_widget.currentTextChanged.connect(self.selectionChanged)

        tab_widget = CfgBase()
        tab_box = QVBoxLayout(self)
        tab_box.addWidget(self.frame_file_selector)
        tab_box.addWidget(self.tab_window)
        tab_widget.setLayout(tab_box)

        splitter = QSplitter()
        splitter.addWidget(list_widget)
        splitter.addWidget(tab_widget)

        #Layout the 2 above widgets vertically
        v_box = QVBoxLayout(self)
        v_box.addWidget(splitter)
        v_box.addWidget(self.button_box)
        self.setLayout(v_box)

        #Populate our Configuration widget with the values from the config file
        if self.var_dict is not None and self.configspec is not None:
            self.affectValuesFromConfig(self.var_dict, self.configspec)

        #No modification in progress for now
        self.setEditInProgress(False)


    def keyPressEvent(self, event):
        """
        Reimplemented keyPressEvent() function so that we can catch and ignore the [ENTER] key
        (When pressed inside a QDialog, this key apply the changes by default)
        """
        if event.key() == QtCore.Qt.Key_Enter or event.key() == QtCore.Qt.Key_Return:
            #key [ENTER]
            event.accept() #We caught the key and we "eat" it, so it prevents its default behaviour
        else:
            #Default behaviour for all the other keys
            QDialog.keyPressEvent(self, event)


    def tr(self, string_to_translate):
        """
        Translate a string using the QCoreApplication translation framework
        @param: string_to_translate: a unicode string
        @return: the translated unicode string if it was possible to translate
        """
        return str(QtCore.QCoreApplication.translate('ConfigWindow', string_to_translate))


    def setEditInProgress(self, edit_mode):
        """
        @param edit_mode: when True, the configuration window swith to edition mode, meaning that the "Apply" and "OK" buttons are enabled, ...
        """
        editor_mode = edit_mode != False
        self.button_box.button(QDialogButtonBox.Apply).setEnabled(editor_mode)
        self.button_box.button(QDialogButtonBox.Discard).setEnabled(editor_mode)
        self.button_box.button(QDialogButtonBox.Close).setEnabled(not editor_mode)
        self.frame_file_selector.setEnabled(not editor_mode)


    def selectionChanged(self, text):
        """
        Slot called when a category is selected in the list of the config widget
        """
        self.tab_window.setCurrentWidget(self.list_items[str(text)])


    def accept(self):
        """
        Check and apply the changes, then close the config window (OK button)
        """
        ok, errors_list = self.validateConfiguration(self.cfg_window_def)
        if ok:
            self.updateConfiguration(self.cfg_window_def, self.var_dict) #Update the configuration dict according to the new settings in our config window
            QDialog.accept(self)
            logger.info('New configuration OK')
            #No more modification in progress
            self.setEditInProgress(False)
        else:
            self.displayMessageBox(errors_list)

    def applyChanges(self):
        """
        Apply changes without closing the window (allow to test some changes without reopening the config window each time)
        """
        ok, errors_list = self.validateConfiguration(self.cfg_window_def)
        if ok:
            self.updateConfiguration(self.cfg_window_def, self.var_dict) #Update the configuration dict according to the new settings in our config window
            self.setResult(ConfigWindow.Applied) #Return a result code that is different from accepted and rejected
            self.finished.emit(self.result())
            logger.info('New configuration applied')
            #No more modification in progress
            self.setEditInProgress(False)
        else:
            self.displayMessageBox(errors_list)

    def reject(self):
        """
        Reload our configuration widget with the values from the config file (=> Cancel the changes in the config window), then close the config window
        """
        self.affectValuesFromConfig(self.var_dict, self.configspec) # cannot be in the if statement - it is possible that the changeOccured was not fired
        if not self.button_box.button(QDialogButtonBox.Close).isEnabled():
            logger.info('New configuration cancelled')
        self.setEditInProgress(False)
        QDialog.reject(self)


    def discardChanges(self):
        """
        Reload our configuration widget with the values from the config file (=> Cancel the changes in the config window). Don't close the config window
        """
        self.affectValuesFromConfig(self.var_dict, self.configspec)
        logger.info('New configuration cancelled')


    def displayMessageBox(self, errors_list):
        """
        Popup a message box in order to display an error message
        @param errors_list: a string that contains all the errors
        """
        errors_list = self.tr('Please correct the following error(s):\n') + errors_list
        error_message = QMessageBox(QMessageBox.Critical, self.tr('Invalid changes'), errors_list);
        error_message.exec_()


    def setConfigSelectorCallback(self, selection_changed_callback, add_file_callback, remove_file_callback, duplicate_file_callback):
        """
        Define the functions called when the config file selector is used (respectively when a new file is selected in the combobox / when a file is added / when a file is removed)
        The ConfigWindow class is just toplevel configuration widget, it doesn't know about anything about the data, hence the callback
        """
        self.selector_change_callback = selection_changed_callback
        self.selector_add_callback = add_file_callback
        self.selector_remove_callback = remove_file_callback
        self.selector_duplicate_callback = duplicate_file_callback


    def setConfigSelectorFilesList(self, config_list, select_item = None):
        """
        Define the functions called when the config file selector is used (respectively when a new file is selected in the combobox / when a file is added / when a file is removed)
        The ConfigWindow class is just toplevel configuration widget, it doesn't know about anything about the data, hence the callback
        """
        if len(config_list) > 0:
            if self.frame_file_selector.layout() is None:
                #There is currently no file selector widget, so we create a new one
                self.cfg_file_selector = CfgComboBox("Choose configuration file:", None, None)
                button_duplicate = QPushButton(QIcon(QPixmap(":/images/layer.png")), "")
                button_duplicate.setToolTip(self.tr("Duplicate the current post-processor"))
                button_add = QPushButton(QIcon(QPixmap(":/images/list-add.png")), "")
                button_add.setToolTip(self.tr("Add a new post-processor with default values"))
                button_remove = QPushButton(QIcon(QPixmap(":/images/list-remove.png")), "")
                button_remove.setToolTip(self.tr("Remove the current post-processor"))

                #Connect the signals to call the callback when an action is done on the file selector
                if self.selector_change_callback is not None:
                    self.cfg_file_selector.combobox.currentIndexChanged[int].connect(self.selector_change_callback)
                button_duplicate.clicked.connect(self.configSelectorDuplicateFile)
                button_add.clicked.connect(self.configSelectorAddFile)
                button_remove.clicked.connect(self.configSelectorRemoveFile)

                layout_file_selector = QHBoxLayout() #For displaying the optional file's selector widget
                layout_file_selector.addWidget(self.cfg_file_selector)
                layout_file_selector.addWidget(button_duplicate)
                layout_file_selector.addWidget(button_add)
                layout_file_selector.addWidget(button_remove)
                self.frame_file_selector.setLayout(layout_file_selector)

            #Fill the combobox with the current file list
            self.cfg_file_selector.setSpec({'string_list': config_list['filename'], 'comment': ''})

            #Select the item if not None
            if select_item is not None:
                self.cfg_file_selector.setValue(select_item)

            #Load the current config
            if self.selector_change_callback is not None:
                self.selector_change_callback(self.cfg_file_selector.combobox.currentIndex())

        else:
            #Item should be a layout or a widget
            logger.warning("At least one config file must be passed to the config selector!")

            #Remove all the files from the config file selector
            if self.cfg_file_selector is not None:
                self.cfg_file_selector.setSpec({'string_list': [], 'comment': ''})


    def configSelectorDuplicateFile(self):
        """
        Function called when the "Remove configuration file" is clicked in the optional config selector zone
        """
        title = self.tr('Duplicate a configuration file')
        label = [self.tr("Enter a new filename (without extension):")]
        value = [""]
        filename_dialog = PopUpDialog(title, label, value)

        if filename_dialog.result is not None and len(filename_dialog.result[0]) > 0:
            #Call the callback function to duplicate the file
            if self.selector_duplicate_callback is not None:
                if self.selector_duplicate_callback(str(self.cfg_file_selector.getValue()), str(filename_dialog.result[0])) == False: #note: str() is needed for PyQT4
                    self.displayMessageBox(self.tr('An error occured while duplicating the file "{0}". Check that it doesn\'t already exists for example'.format(filename_dialog.result[0])))
            else:
                logger.warning("No callback defined for duplicating the file, nothing will happen!")


    def configSelectorAddFile(self):
        """
        Function called when the "Remove configuration file" is clicked in the optional config selector zone
        """
        title = self.tr('Add a configuration file')
        label = [self.tr("Enter filename (without extension):")]
        value = [""]
        filename_dialog = PopUpDialog(title, label, value)

        if filename_dialog.result is not None and len(filename_dialog.result[0]) > 0:
            if self.selector_add_callback is not None:
                if self.selector_add_callback(str(filename_dialog.result[0])) == False:
                    self.displayMessageBox(self.tr('An error occured while creating the file "{0}". Check that it doesn\'t already exists for example'.format(filename_dialog.result[0])))
            else:
                logger.warning("No callback defined for adding the file, nothing will happen!")


    def configSelectorRemoveFile(self):
        """
        Function called when the "Remove configuration file" is clicked in the optional config selector zone
        """
        confirmation_result = QMessageBox.question(self, self.tr('Delete configuration file?'), self.tr('Are you sure you want to permanently remove the file "{0}"'.format(self.cfg_file_selector.getValue())), QMessageBox.Ok | QMessageBox.Cancel);
        if confirmation_result == QMessageBox.Yes or confirmation_result == QMessageBox.Ok:
            #User has confirmed the file suppression, so let's go
            if self.selector_remove_callback is not None:
                if self.selector_remove_callback(str(self.cfg_file_selector.getValue())) == False:
                    self.displayMessageBox(self.tr('An error occured while removing the file "{0}". Remove it manually'.format(self.cfg_file_selector.getValue())))
            else:
                logger.warning("No callback defined for removing the file, nothing will happen!")


    def createWidgetFromDefinitionDict(self):
        """
        Automatically build a widget, based on dict definition of the items.
        @return: a QWidget containing all the elements of the configuration window
        """
        logger.info('Creating configuration window')
        definition = self.cfg_window_def

        tab_widgets = OrderedDict()

        #Create a dict with the sections' titles if not already defined. This dict contains sections' names as key and tabs' titles as values
        if '__section_title__' not in definition:
            definition['__section_title__'] = {}

        #Compute all the sections
        for section in definition:
            #skip the special section __section_title__
            if section == '__section_title__':
                continue

            #Create the title for the section if it doesn't already exist
            if section not in definition['__section_title__']:
                #The title for this section doesn't exist yet
                if isinstance(definition[section], dict) and '__section_title__' in definition[section]:
                    #The title for this section is defined into the section itself => we add the title to the dict containing all the titles
                    definition['__section_title__'][section] = definition[section]['__section_title__']
                else:
                    #The title for this section is not defined anywhere, so we use the section name itself as a title
                    definition['__section_title__'][section] = section.replace('_', ' ')

            #Create the tab (and the widget) for the current section, if it doesn't exist yet
            widget = None
            for widget_label in tab_widgets:
                if definition['__section_title__'][section] == widget_label:
                    widget = tab_widgets[widget_label]
                    break

            if widget is None:
                widget = QWidget()
                tab_widgets[definition['__section_title__'][section]] = widget

            #Create the tab content for this section
            self.createWidgetSubSection(definition[section], widget)

            #Add a stretch at the end of this subsection
            if widget.layout() is not None:
                widget.layout().addStretch()

        #Add a QSpacer at the bottom of each widget, so that the items are placed on top of each tab
        for widget in tab_widgets.values():
            if widget.layout() is not None:
                widget.layout().addStretch()

        return tab_widgets


    def createWidgetSubSection(self, subdefinition, section_widget):
        """
        Create the widgets that will be inserted into the tabs of the configuration window
        @param subdefinition: part of the definition dict
        @param section_widget: the widget that host the subwidgets
        @return: section_widget (for recursive call)
        """
        vertical_box = section_widget.layout()
        if vertical_box is None:
            vertical_box = QVBoxLayout()
            section_widget.setLayout(vertical_box)
        vertical_box.setSpacing(0) #Don't use too much space, it makes the option window too big otherwise

        if isinstance(subdefinition, dict):
            vertical_box.addWidget(subdefinition.get('__subtitle__', CfgSubtitle()))

        self.createWidgetSubSectionWithSubLevels(subdefinition, section_widget)


    def createWidgetSubSectionWithSubLevels(self, subdefinition, section_widget):
        """
        Create the widgets that will be inserted into the tabs of the configuration window
        @param subdefinition: part of the definition dict
        @param section_widget: the widget that host the subwidgets
        @return: section_widget (for recursive call)
        """

        vertical_box = section_widget.layout()

        if isinstance(subdefinition, dict):
            for subsection in subdefinition:
                if subsection == '__section_title__':
                    #skip the special section
                    continue

                #Browse sublevels
                self.createWidgetSubSectionWithSubLevels(subdefinition[subsection], section_widget) #Recursive call, all the nested configuration item will appear at the same level
        else:
            if isinstance(subdefinition, (QWidget, QLayout)):
                vertical_box.addWidget(subdefinition)
                if hasattr(subdefinition, 'setChangeSlot'):
                    subdefinition.setChangeSlot(self.changeOccured)
            else:
                #Item should be a layout or a widget
                logger.error("item subdefinition is incorrect")

        return section_widget


    def affectValuesFromConfig(self, config, configspec):
        """
        Affect new values for the configuration
        @param config: data readed from the configfile. This dict is created by ConfigObj module.
        @param configspec: specifications of the configfile. This variable is created by ConfigObj module.
        """
        self.var_dict = config #This is the data from the configfile (dictionary created by ConfigObj class)
        self.configspec = configspec #This is the specifications for all the entries defined in the config file

        self.setValuesFromConfig(self.cfg_window_def, self.var_dict, self.configspec)

        #No modification in progress for now
        self.setEditInProgress(False)

    def setValuesFromConfig(self, window_def, config, configspec):
        """
        This function populates the option widget with the values that come from the configuration file.
        The values from the configuration file are stored into a dictionary, we browse this dictionary to populate our window
        @param window_def: the dict that describes our window
        @param config: data readed from the configfile. This dict is created by ConfigObj module.
        @param configspec: specifications of the configfile. This variable is created by ConfigObj module.
        """
        #Compute all the sections
        for section in window_def:
            #skip the special section __section_title__
            if section == '__section_title__' or isinstance(window_def[section], CfgDummy):
                continue

            if config is not None and section in config:
                if isinstance(window_def[section], dict):
                    #Browse sublevels
                    configspec_sub = None
                    if configspec is not None and section in configspec:
                        configspec_sub = configspec[section]
                    self.setValuesFromConfig(window_def[section], config[section], configspec_sub) #Recursive call, until we find a real item (not a dictionnary with subtree)
                else:
                    if isinstance(window_def[section], (QWidget, QLayout)):
                        #assign the configuration retrieved from the configspec object of the ConfigObj
                        if configspec is not None and section in configspec:
                            window_def[section].setSpec(self.configspecParser(configspec[section], configspec.comments[section]))
                        #assign the value that was readed from the configfile
                        window_def[section].setValue(config[section])
                    else:
                        #Item should be a layout or a widget
                        logger.warning("item {0} is not a widget, can't set it's value!".format(window_def[section]))
            else:
                logger.error("can't assign values, item or section {0} not found in config file!".format(section))


    def configspecParser(self, configspec, comments):
        """
        This is a really trivial parser for ConfigObj spec file. This parser aims to exctract the limits and the available options for the entries in the config file. For example:
        if a config entry is defined as "option('mm', 'in', default = 'mm')", then the parser will create a list with ['mm', 'in]
        similarly, if an entry defined as "integer(max=9)", the max value will be exctracted
        @param configspec: specifications of the configfile. This variable is created by ConfigObj module.
        @param comments: string list containing the comments for a given item
        @return The function returns a dictionary with the following fields
        - minimum : contains the minimum value or length for an entry (possibly 'None' if nothing found)
        - maximum : contains the maximum value or length for an entry (possibly 'None' if nothing found)
        - string_list : contains the list of options for an "option" field, or the column titles for a table
        - comment : a text with the comment that belongs to the parameter (possibly an empty string if nothing found)
        """
        #logger.debug('configspecParser({0}, {1})'.format(configspec, comments))
        minimum = None
        maximum = None
        string_list = []

        if isinstance(configspec, dict):
            #If the received configspec is a dictionary, we most likely have a table, so we are going to exctract sections names of this table

                #When tables are used, the "__many__" config entry is used for the definition of the configspec, so we try to excract the sections names by using this __many__ special keyword.
                #Example: 'Tool_Parameters': {[...], '__many__': {'diameter': 'float(default = 3.0)', 'speed': 'float(default = 6000)', 'start_radius': 'float(default = 3.0)'}}
                if '__many__' in configspec and isinstance(configspec['__many__'], dict):
                    string_list = configspec['__many__'].keys()
                    string_list.insert(0, '') #prepend an empty element since the first column of the table is the row name (eg a unique tool number)

        else:
            #configspec is normaly a string from which we can exctrat min / max values and possibly a list of options

            #Handle "option" config entries
            string_list = self.configspecParserExctractSections('option', configspec)
            i = 0
            while i < len(string_list): #DON'T replace this with a "for", it would silently skip some steps because we remove items inside the loop
                #remove unwanted items which are unquoted (like the "default=" parameter) and remove the quotes
                if string_list[i].startswith('"'):
                    string_list[i] = string_list[i].strip('"')
                elif string_list[i].startswith("'"):
                    string_list[i] = string_list[i].strip("'")
                else:
                    #unwanted item, it doesn't contain an element of the option()
                    del string_list[i]
                    continue

                i += 1

            #Handle "integer" and "string" config entries
            if len(string_list) <= 0:
                string_list = self.configspecParserExctractSections('integer', configspec)
                if len(string_list) <= 0:
                    string_list = self.configspecParserExctractSections('string', configspec)

                minimum, maximum = self.handle_type_config_entries(minimum, maximum, string_list, toInt)

            #Handle "float" config entries
            if len(string_list) <= 0:
                string_list = self.configspecParserExctractSections('float', configspec)

                minimum, maximum = self.handle_type_config_entries(minimum, maximum, string_list, toFloat)

        #Handle comments: comments are stored in a list and contains any chars that are in the configfile (including the hash symbol and the spaces)
        comments_string = ''
        if len(comments) > 0:
            for comment in comments:
                comments_string += comment.strip()

            comments_string = comments_string.strip(' #')
            comments_string = comments_string.replace('#', '\n')

        logger.debug('configspecParser(): exctracted option elements = {0}, min = {1}, max = {2}, comment = {3}'.format(string_list, minimum, maximum, comments_string))

        result = {}
        result['minimum'] = minimum
        result['maximum'] = maximum
        result['string_list'] = string_list
        result['comment'] = comments_string
        return result

    def handle_type_config_entries(self, minimum, maximum, string_list, type_converter):
        for element in string_list:
            if minimum is not None and maximum is not None:
                break

            value = type_converter(element)
            if value[1]:
                if minimum is None:
                    minimum = value[0]
                elif maximum is None:
                    maximum = value[0]

            if minimum is None and 'min' in element:
                # string found in a string like "min = -7"
                element = element.replace('min', '')
                element = element.strip(' =')
                value = type_converter(element)
                if value[1]:
                    minimum = value[0]

            if maximum is None and 'max' in element:
                # 'max' string found
                element = element.replace('max', '')
                element = element.strip(' =')
                value = type_converter(element)
                if value[1]:
                    maximum = value[0]

        return minimum, maximum

    def configspecParserExctractSections(self, attribute_name, string):
        """
        returns a list of item from a string. Eg the string "option('mm', 'in', default = 'mm')" will be exploded into the string list ["mm", "in", "default = 'mm'"]
        """
        string_list = []

        pos_init = string.find(attribute_name + '(')
        if pos_init >= 0:
            pos_init += len(attribute_name + '(') #skip the "option("

            pos_end = string.find(')', pos_init)
            if pos_end > pos_init:
                #print("substring found = {0}".format(string[pos_init:pos_end]))
                string_list = string[pos_init:pos_end].split(',')

        # remove empty elements and remove leading and trailing spaces
        string_list = [string.strip() for string in string_list if string]
        return string_list


    def changeOccured(self):
        """
        This function (slot) is called whenever a modification occurs in the configuration window.
        It enables "Apply" and "OK" buttons, plus disable the configfile selector.
        """
        #There are some changes, we swith to edit mode
        self.setEditInProgress(True)


    def validateConfiguration(self, window_def, result_string = '', result_bool = True):
        """
        Check the configuration (check the limits, eg min/max values, ...). These limits are set according to the configspec passed to the constructor
        @param window_def: the dict that describes our window
        @param result_string: use only for recursive call
        @param result_bool: use only for recursive call
        @return (result_bool, result_string):
         - result_bool: True if no errors were encountered, False otherwise
         - result_string: a string containing all the errors encountered during the validation
        """
        #Compute all the sections
        for section in window_def:
            #skip the special section __section_title__
            if section == '__section_title__' or isinstance(window_def[section], CfgDummy):
                continue

            if isinstance(window_def[section], dict):
                #Browse sublevels
                (result_bool, result_string) = self.validateConfiguration(window_def[section], result_string, result_bool) #Recursive call, until we find a real item (not a dictionnary with subtree)
            else:
                if isinstance(window_def[section], (QWidget, QLayout)):
                    #check that the value is correct for each widget
                    result = window_def[section].validateValue()
                    if result[0] is False: result_bool = False
                    result_string += result[1]
                else:
                    #Item should be a layout or a widget
                    logger.warning("item {0} is not a widget, can't validate it!".format(window_def[section]))

        return (result_bool, result_string)


    def updateConfiguration(self, window_def, config):
        """
        Update the application configuration (ConfigObj) according to the changes made into the ConfigWindow.
        The self.var_dict variable is updated
        @param window_def: the dict that describes our window
        @param config: data readed from the configfile. This dict is created by ConfigObj module and will be updated here.
        """
        #Compute all the sections
        for section in window_def:
            #skip the special section __section_title__
            if section == '__section_title__' or isinstance(window_def[section], CfgDummy):
                continue

            if config is not None and section in config:
                if isinstance(window_def[section], dict):
                    #Browse sublevels
                    self.updateConfiguration(window_def[section], config[section]) #Recursive call, until we find a real item (not a dictionnary with subtree)
                else:
                    if isinstance(window_def[section], (QWidget, QLayout)):
                        #assign the value that was readed from the configfile
                        config[section] = window_def[section].getValue()
                    else:
                        #Item should be a layout or a widget
                        logger.warning("item {0} is not a widget, can't update it!".format(window_def[section]))
            else:
                logger.error("can't update configuration, item or section {0} not found in config file!".format(section))



############################################################################################################################
# The classes below are all based on QWidgets and allow to create various predefined elements for the configuration window #
############################################################################################################################

class CfgBase(QWidget):
    """
    Base class used only for setting the Layout. Want a consistent look.
    """
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)

    def setLayout(self, layout=None, indent=True):
        layout.setSpacing(2)  # Don't use too much space, it makes the option window too big otherwise
        layout.setContentsMargins(10 if indent else 0, 5, 1, 1)
        QWidget.setLayout(self, layout)


class CfgDummy(CfgBase):
    """
    If a class inherits this dummy class then it should be skipped - it only serves display purposes
    """
    def __init__(self, parent=None):
        CfgBase.__init__(self, parent)


class CfgSubtitle(CfgDummy):
    def __init__(self, text=None, parent=None):
        CfgDummy.__init__(self, parent)

        layout = QHBoxLayout()

        if text is not None:
            layout.addWidget(QLabel(text))

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setSizePolicy(QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed))
        layout.addWidget(separator)

        self.setLayout(layout, False)


class CfgCheckBox(CfgBase):
    """
    Subclassed QCheckBox to match our needs.
    """

    def __init__(self, text, tristate = False, parent = None):
        """
        Initialization of the CfgCheckBox class.
        @param text: text string associated with the checkbox
        @param tristate: whether the checkbox must have 3 states (tristate) or 2 states
        """
        CfgBase.__init__(self, parent)

        self.checkbox = QCheckBox(text, parent)
        self.checkbox.setTristate(tristate)

        layout = QHBoxLayout(parent)
        layout.addWidget(self.checkbox)
        self.setLayout(layout)

    def setSpec(self, spec):
        """
        Set the specifications for the item (min/max values, ...)
        @param spec: the specifications dict (can contain the following keys: minimum, maximum, comment, string_list)
        """
        #Nothing is configurable in the configspec for this item
        if spec['comment']:
            self.setWhatsThis(spec['comment'])

    def setChangeSlot(self, changeNotifyer):
        """
        Assign a notifyier slot (this slot is called whenever the state of the widget changes)
        @param changeNotifyer: the function (slot) that is called in case of change
        """
        self.checkbox.stateChanged.connect(changeNotifyer)

    def validateValue(self):
        """
        This item can't be wrong, so we always return true and an empty string
        @return (True, ''):
        """
        return (True, '')

    def getValue(self):
        """
        @return 0 when the checkbox is unchecked, 1 if it is checked and 2 if it is partly checked (tristate must be set to true for tristate mode)
        """
        check_state = self.checkbox.checkState()
        if check_state == QtCore.Qt.Unchecked:
            check_state = 0
        elif check_state == QtCore.Qt.Checked:
            check_state = 1
        elif check_state == QtCore.Qt.PartiallyChecked:
            check_state = 2

        return check_state if self.checkbox.isTristate() else check_state == 1

    def setValue(self, value):
        """
        Assign the value for our object
        @param value: 0 when the checkbox is unchecked, 1 if it is checked and 2 if it is partly checked (tristate must be set to true for tristate mode)
        """
        self.blockSignals(True) # Avoid unnecessary signal (we don't want the config window to emit any signal when filling the fields programatically)
        if value == 0:
            self.checkbox.setCheckState(QtCore.Qt.Unchecked)
        elif value == 2:
            self.checkbox.setCheckState(QtCore.Qt.PartiallyChecked)
        else:
            self.checkbox.setCheckState(QtCore.Qt.Checked)
        self.blockSignals(False)


class CfgSpinBox(CfgBase):
    """
    Subclassed QSpinBox to match our needs.
    """

    def __init__(self, text, unit = None, minimum = None, maximum = None, parent = None):
        """
        Initialization of the CfgSpinBox class (used for int values).
        @param text: text string associated with the SpinBox
        @param minimum: min value (int)
        @param minimum: max value (int)
        """
        CfgBase.__init__(self, parent)

        self.label = QLabel(text, parent)

        self.spinbox = QSpinBox(parent)
        self.spinbox.setMinimumWidth(200)  # Provide better alignment with other items

        if unit is not None:
            self.setUnit(unit)

        layout = QHBoxLayout(parent)
        layout.addWidget(self.label)
        layout.addStretch()
        layout.addWidget(self.spinbox)
        self.setLayout(layout)

        self.setSpec({'minimum': minimum, 'maximum': maximum, 'comment': ''})

    def setSpec(self, spec):
        """
        Set the specifications for the item (min/max values, ...)
        @param spec: the specifications dict (can contain the following keys: minimum, maximum, comment, string_list)
        """
        if spec['minimum'] is not None:
            self.spinbox.setMinimum(spec['minimum'])
        else:
            self.spinbox.setMinimum(-1000000000) #if no value is defined for the minimum, use a reasonable value

        if spec['maximum'] is not None:
            self.spinbox.setMaximum(spec['maximum'])
        else:
            self.spinbox.setMaximum(1000000000) #if no value is defined for the maximum, use a more reasonable value than 99 (default value in QT) ...

        if spec['comment']:
            self.setWhatsThis(spec['comment'])

    def setChangeSlot(self, changeNotifyer):
        """
        Assign a notifyier slot (this slot is called whenever the state of the widget changes)
        @param changeNotifyer: the function (slot) that is called in case of change
        """
        self.spinbox.valueChanged.connect(changeNotifyer)

    def setUnit(self, unit):
        """
        Set the unit of the SpinBox (unit is displayed just after the value)
        @param unit: string with the unit used for the spinbox
        """
        self.spinbox.setSuffix(unit)

    def validateValue(self):
        """
        This item can't be wrong, so we always return true and an empty string
        @return (True, ''):
        """
        return (True, '')

    def getValue(self):
        """
        @return: the current value of the QSpinBox
        """
        return self.spinbox.value()

    def setValue(self, value):
        """
        Assign the value for our object
        @param value: int value
        """
        self.spinbox.blockSignals(True) # Avoid unnecessary signal (we don't want the config window to emit any signal when filling the fields programatically)
        self.spinbox.setValue(value)
        self.spinbox.blockSignals(False)


class CorrectedDoubleSpinBox(QDoubleSpinBox):
    """
    Subclassed QDoubleSpinBox to get a version that works for everyone ...
    DON'T remove this class, it is a correction for the guys who decided to use comma (',') as a decimal separator (France, Italy, ...) but failed to use comma on the keypad (keypad use dot, not comma)!
    This subclassed QDoubleSpinBox allow to enter decimal values like 3.5 _and_ 3,5
    (the default QDoubleSpinBox implementation only allow the locale as a decimal separator, so for eg, France, you just can't enter decimal values using the keypad!)
    See here for more details: http://www.qtcentre.org/threads/12483-Validator-for-QDoubleSpinBox and http://www.qtcentre.org/threads/13711-QDoubleSpinBox-dot-as-comma
    """

    def __init__(self, parent = None):
        QDoubleSpinBox.__init__(self, parent)
        self.saved_suffix = ''
        #Let's use the locale decimal separator if it is different from the dot ('.')
        local_decimal_separator = QLocale().decimalPoint()
        if local_decimal_separator == '.':
            local_decimal_separator = ''
        self.lineEdit().setValidator(QRegExpValidator(QRegExp("-?[0-9]*[.{0}]?[0-9]*.*".format(local_decimal_separator)), self))

    def setSuffix(self, suffix):
        self.saved_suffix = suffix
        QDoubleSpinBox.setSuffix(self, suffix)

    def valueFromText(self, text):
        # result = float(text.replace('.', QLocale().decimalPoint()))
        # python expect a dot ('.') as decimal separator
        text = qstr_encode(text).replace(str_encode(self.saved_suffix), '').replace(str(QLocale().decimalPoint()), '.')
        return toFloat(text)[0]

    def validate(self, entry, pos):
        #let's *really* trust the validator
        #http://python.6.x6.nabble.com/QValidator-raises-TypeError-td1923683.html
        #print("validate({}, {})".format(entry, pos))
        return (QValidator.Acceptable, entry, pos)


class CfgDoubleSpinBox(CfgSpinBox):
    """
    Subclassed QDoubleSpinBox to match our needs.
    """

    def __init__(self, text, unit = None, minimum = None, maximum = None, precision = None, parent = None):
        """
        Initialization of the CfgDoubleSpinBox class (used for float values).
        @param text: text string associated with the SpinBox
        @param minimum: min value (float)
        @param minimum: max value (float)
        """
        CfgBase.__init__(self, parent)  # skip the init of CfgSpinBox - we want a "corrected" spinbox

        self.label = QLabel(text, parent)

        self.spinbox = QSpinBox(parent)
        self.spinbox = CorrectedDoubleSpinBox(parent)
        self.spinbox.setMinimumWidth(200)  # Provide better alignment with other items
        if precision is not None:
            self.spinbox.setDecimals(precision)

        if unit is not None:
            self.setUnit(unit)

        layout = QHBoxLayout(parent)
        layout.addWidget(self.label)
        layout.addStretch()
        layout.addWidget(self.spinbox)
        self.setLayout(layout)

        self.setSpec({'minimum': minimum, 'maximum': maximum, 'comment': ''})


class CfgLineEdit(CfgBase):
    """
    Subclassed QLineEdit to match our needs.
    """

    def __init__(self, text, size_min = None, size_max = None, parent = None):
        """
        Initialization of the CfgLineEdit class (text edit, one line).
        @param text: text string associated with the line edit
        @param size_min: min length (int)
        @param size_max: max length (int)
        """
        CfgBase.__init__(self, parent)

        self.label = QLabel(text, parent)

        self.lineedit = QLineEdit(parent)

        layout = QVBoxLayout(parent)
        layout.addWidget(self.label)
        layout.addWidget(self.lineedit)
        self.setLayout(layout)

        self.size_min = 0
        self.setSpec({'minimum': size_min, 'maximum': size_max, 'comment': ''})

    def setSpec(self, spec):
        """
        Set the specifications for the item (min/max values, ...)
        @param spec: the specifications dict (can contain the following keys: minimum, maximum, comment, string_list)
        """
        if spec['minimum'] is not None:
            self.size_min = spec['minimum']

        if spec['maximum'] is not None:
            self.lineedit.setMaxLength(spec['maximum'])

        if spec['comment']:
            self.setWhatsThis(spec['comment'])

    def setChangeSlot(self, changeNotifyer):
        """
        Assign a notifyier slot (this slot is called whenever the state of the widget changes)
        @param changeNotifyer: the function (slot) that is called in case of change
        """
        self.lineedit.textChanged.connect(changeNotifyer)

    def validateValue(self):
        """
        Check the minimum length value
        @return (result_bool, result_string):
         - result_bool: True if no errors were encountered, False otherwise
         - result_string: a string containing all the errors encountered during the validation
        """
        field_length = len(str(self.lineedit.text()))
        if field_length < self.size_min:
            result = (False, str(self.tr('\nNot enough chars (expected {0}, found {1}) for the field "{2}"\n')).format(self.size_min, field_length, self.label.text()))
        else:
            #OK
            result = (True, '')
        return result

    def getValue(self):
        """
        @return: the current value of the QSpinBox
        """
        return str(self.lineedit.text())

    def setValue(self, value):
        """
        Assign the value for our object
        @param value: text string
        """
        self.lineedit.blockSignals(True) # Avoid unnecessary signal (we don't want the config window to emit any signal when filling the fields programatically)
        self.lineedit.setText(str(value))
        self.lineedit.blockSignals(False)


class CfgListEdit(CfgLineEdit):
    """
    Subclassed QLineEdit to match our needs.
    """

    def __init__(self, text, separator, size_max = None, parent = None):
        """
        Initialization of the CfgListEdit class (text edit, one line, strings separated with "separator").
        @param text: text string associated with the line edit
        @param separator: the separator used for the strings (eg: ',')
        @param size_min: min length (int)
        @param size_max: max length (int)
        """
        CfgLineEdit.__init__(self, text + " (use '" + separator + "' as separator)", size_max, parent)
        #Store the separator so that we can return a list of strings instead of a single string
        self.separator = separator

    def getValue(self):
        """
        @return the current value of the QSpinBox (string list)
        """
        item_list = str(self.lineedit.text()).split(self.separator)
        item_list = [item.strip(' ') for item in item_list]  # remove leading and trailing whitespaces
        return item_list

    def setValue(self, value):
        """
        Assign the value for our object
        @param value: text string or list of text strings
        """
        joined_value = value
        if isinstance(value, (list, tuple)):
            joined_value = (self.separator + ' ').join(value) #Join the strings and add a space for more readability (the space will be removed when writting)

        self.lineedit.setText(joined_value)


class CfgTextEdit(CfgBase):
    """
    Subclassed QTextEdit to match our needs.
    """

    def __init__(self, text, size_min = None, size_max = None, parent = None):
        """
        Initialization of the CfgLineEdit class (text edit, one line).
        @param text: text string associated with the line edit
        @param size_min: min length (int)
        @param size_max: max length (int)
        """
        CfgBase.__init__(self, parent)

        self.label = QLabel(text, parent)

        self.textedit = QTextEdit(parent)
        self.textedit.setAcceptRichText(False)
        self.textedit.setAutoFormatting(QTextEdit.AutoNone)

        layout = QVBoxLayout(parent)
        layout.addWidget(self.label)
        layout.addWidget(self.textedit)
        self.setLayout(layout)

        self.size_min = 0
        self.setSpec({'minimum': size_min, 'maximum': size_max, 'comment': ''})

    def setSpec(self, spec):
        """
        Set the specifications for the item (min/max values, ...)
        @param spec: the specifications dict (can contain the following keys: minimum, maximum, comment, string_list)
        """
        if spec['minimum'] is not None:
            self.size_min = spec['minimum']

        if spec['maximum'] is not None:
            self.textedit.setMaxLength(spec['maximum'])

        if spec['comment']:
            self.setWhatsThis(spec['comment'])

    def setChangeSlot(self, changeNotifyer):
        """
        Assign a notifyier slot (this slot is called whenever the state of the widget changes)
        @param changeNotifyer: the function (slot) that is called in case of change
        """
        self.textedit.textChanged.connect(changeNotifyer)

    def validateValue(self):
        """
        Check the minimum length value
        @return (result_bool, result_string):
         - result_bool: True if no errors were encountered, False otherwise
         - result_string: a string containing all the errors encountered during the validation
        """
        field_length = len(str(self.textedit.toPlainText()))
        if field_length < self.size_min:
            result = (False, str(self.tr('\nNot enough chars (expected {0}, found {1}) for the field "{2}"\n')).format(self.size_min, field_length, self.label.text()))
        else:
            #OK
            result = (True, '')
        return result

    def getValue(self):
        """
        @return: the current value of the QSpinBox
        """
        return str(self.textedit.toPlainText())

    def setValue(self, value):
        """
        Assign the value for our object
        @param value: text string
        """
        self.textedit.blockSignals(True) # Avoid unnecessary signal (we don't want the config window to emit any signal when filling the fields programatically)
        self.textedit.setPlainText(value)
        self.textedit.blockSignals(False)


class CfgComboBox(CfgBase):
    """
    Subclassed QComboBox to match our needs.
    """

    def __init__(self, text, items_list = None, default_item = None, parent = None):
        """
        Initialization of the CfgComboBox class (drop-down menu).
        @param text: text string associated with the combobox
        @param items_list: string list containing all the available options
        @param default_item: string containing the default selected item
        """
        CfgBase.__init__(self, parent)

        if isinstance(items_list, (list, tuple)):
            self.setSpec({'string_list': items_list, 'comment': ''})
        if default_item is not None:
            self.setValue(default_item)

        self.label = QLabel(text, parent)

        self.combobox = QComboBox(parent)
        self.combobox.setMinimumWidth(200)  # Provide better alignment with other items

        layout = QHBoxLayout(parent)
        layout.addWidget(self.label)
        layout.addStretch()
        layout.addWidget(self.combobox)
        self.setLayout(layout)

    def setSpec(self, spec):
        """
        Set the specifications for the item (min/max values, ...)
        @param spec: the specifications dict (can contain the following keys: minimum, maximum, comment, string_list)
        """
        self.combobox.blockSignals(True) # Avoid unnecessary signal (we don't want the config window to emit any signal when filling the fields programatically)
        self.combobox.clear()
        self.combobox.addItems(spec['string_list'])

        if spec['comment']:
            self.setWhatsThis(spec['comment'])
        self.combobox.blockSignals(False)

    def setChangeSlot(self, changeNotifyer):
        """
        Assign a notifyier slot (this slot is called whenever the state of the widget changes)
        @param changeNotifyer: the function (slot) that is called in case of change
        """
        self.combobox.currentIndexChanged.connect(changeNotifyer)

    def validateValue(self):
        """
        This item can't be wrong, so we always return true and an empty string
        @return (True, ''):
        """
        return (True, '')

    def getValue(self):
        """
        @return: the string of the currently selected entry
        """
        return self.combobox.currentText()

    def setValue(self, value):
        """
        Assign the value for our object
        @param value: the text of the entry to select in the combobox
        """
        self.combobox.blockSignals(True) # Avoid unnecessary signal (we don't want the config window to emit any signal when filling the fields programatically)
        self.combobox.setCurrentIndex(self.combobox.findText(value)) #Compatible with both PyQt4 and PyQt5
        self.combobox.blockSignals(False)


class CfgTable(QWidget):
    """
    Subclassed QTableWidget to match our needs.
    """
    #Define a QT signal that is emitted when the table is modified.
    #Note: this signal is not emitted in this class ; it is up to the subclasses to emit it
    tableChanged = QtCore.pyqtSignal()

    def __init__(self, text, columns = None, parent = None):
        """
        Initialization of the CfgTable class (editable 2D table).
        @param text: text string associated with the table
        @param columns: string list containing all the columns names
        """
        QWidget.__init__(self, parent)

        self.tablewidget = QTableWidget(parent)
        self.tablewidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        if isinstance(columns, (list, tuple)):
            self.setSpec({'string_list': columns, 'comment': ''})
        else:
            self.keys = [] #No columns yet
        self.tablewidget.horizontalHeader().setStretchLastSection(True)
        self.tablewidget.horizontalHeader().sectionClicked.connect(self.tablewidget.clearSelection) #Allow to unselect the lines by clicking on the column name (useful to add a line at the end)

        self.label = QLabel(text, parent)
        self.button_add = QPushButton(QIcon(QPixmap(":/images/list-add.png")), "")
        self.button_remove = QPushButton(QIcon(QPixmap(":/images/list-remove.png")), "")
        self.button_add.clicked.connect(self.appendLine)
        self.button_remove.clicked.connect(self.removeLine)
        self.layout_button = QVBoxLayout()
        self.layout_button.addWidget(self.button_add)
        self.layout_button.addWidget(self.button_remove)

        self.layout_table = QHBoxLayout()
        #self.tablewidget.setSizePolicy(size_policy)
        self.layout_table.addWidget(self.tablewidget)
        self.layout_table.addLayout(self.layout_button)

        self.layout = QVBoxLayout(parent)

        self.layout.addWidget(self.label)
        self.layout.addLayout(self.layout_table)
        self.setLayout(self.layout)

        #Ensure that the table always expand to the maximum available space
        size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        size_policy.setVerticalStretch(10)
        size_policy.setHorizontalStretch(10)
        self.setSizePolicy(size_policy)

    def setSpec(self, spec):
        """
        Set the specifications for the item (min/max values, ...)
        @param spec: the specifications dict (can contain the following keys: minimum, maximum, comment, string_list)
        """
        self.keys = spec['string_list']
        if len(self.keys) > 0 and not self.keys[0]:
            self.keys[0] = 'name' #name of first column is normaly undefined in configspec, so we use a generic name, just to display something in the header of the QTable
        self.tablewidget.setColumnCount(len(self.keys))
        self.tablewidget.setHorizontalHeaderLabels(self.keys)

        if spec['comment']:
            self.setWhatsThis(spec['comment'])

    def setChangeSlot(self, changeNotifyer):
        """
        Assign a notifyier slot (this slot is called whenever the state of the widget changes)
        @param changeNotifyer: the function (slot) that is called in case of change
        """
        self.tableChanged.connect(changeNotifyer)
        self.tablewidget.itemChanged.connect(changeNotifyer)
        self.tablewidget.cellChanged.connect(changeNotifyer)
        self.button_add.clicked.connect(changeNotifyer)
        self.button_remove.clicked.connect(changeNotifyer)

    def appendLine(self, line = None):
        """
        Add a line to the table. The new line is inserted before the selected line, or at the end of the table is no line is selected
        @param line: a string list containing all the values for this lines. If line is None, an empty line is inserted
        """
        selected_row = self.tablewidget.currentRow()
        if selected_row < 0 or len(self.tablewidget.selectedIndexes()) <= 0: #Trick to be able to insert lines before the first and after the last line (click on column name to unselect the lines)
            selected_row = self.tablewidget.rowCount()

        self.tablewidget.insertRow(selected_row)

        #If provided, fill the table with the content of the line list
        if line is not None and isinstance(line, (list, tuple)) and len(line) >= self.tablewidget.columnCount():
            for i in range(self.tablewidget.columnCount()):
                #self.tablewidget.setItem(selected_row, i, QTableWidgetItem(line[i]))
                self.setCellValue(selected_row, i, line[i])
        else:
            for i in range(self.tablewidget.columnCount()):
                self.setCellValue(selected_row, i, "") #Don't remove this line, otherwise the subclasses won't be able to set custom widget into the table.

        #Resize the columns to the content, except for the last one
        for i in range(self.tablewidget.columnCount() - 1):
            self.tablewidget.resizeColumnToContents(i)

        #Resize the rows to the content
        for i in range(self.tablewidget.rowCount()):
            self.tablewidget.resizeRowToContents(i)

    def removeLine(self):
        """
        Remove a line from the table. The selected line is suppressed, or the last line if no line is selected
        """
        selected_row = self.tablewidget.currentRow()
        if selected_row < 0 and self.tablewidget.rowCount() > 0:
            selected_row = self.tablewidget.rowCount() - 1

        if selected_row >= 0:
            self.tablewidget.removeRow(selected_row)

    def setCellValue(self, line, column, value):
        """
        Default implementation for filling cells use Qt default QTableWidgetItem. One can subclass to provide another implementation, like inserting various Widget into the table.
        @param line: line number (int)
        @param column: column number (int)
        @param value: cell content (string)
        """
        self.tablewidget.blockSignals(True) # Avoid unnecessary signal (we don't want the config window to emit any signal when filling the fields programatically)
        self.tablewidget.setItem(line, column, QTableWidgetItem(value))
        self.tablewidget.blockSignals(False)

    def validateValue(self):
        """
        Default implementation always return true (OK) and an empty string
        @return (True, ''):
        """
        return (True, '')

    def getValue(self):
        """
        @return: a nested dictionnary that can be directly used to update the ConfigObj (class that handles configuration file)
        Example of returned value:
        {'pause': {'gcode': 'M5 (Spindle off)\nM9 (Coolant off)\nM0\n\nM8\nS5000M03 (Spindle 5000rpm cw)\n'}, 'probe_tool': {'gcode': '\nO<Probe_Tool> CALL\nS6000 M3 M8\n'}}
        """
        result_dict = {}
        for i in range(self.tablewidget.rowCount()):
            key = self.tablewidget.item(i, 0)
            if not key:
                continue
            key = str(key.text())
            if not key:
                continue
            result_dict[key] = {}

            j = 1
            while j < self.tablewidget.columnCount():
                sub_key = self.keys[j] #Column name
                value = self.tablewidget.item(i, j)
                if not value:
                    j += 1
                    continue
                value = str(value.text())
                if sub_key is not None:
                    result_dict[key][sub_key] = value
                j += 1

        return result_dict

    def setValue(self, value):
        """
        Assign the value for our object
        @param value: this is a nested dict, with keys going to the first column of our table and values going to the other columns. Example of received value:
        {'15': {'diameter': 1.5, 'speed': 6000.0, 'start_radius': 1.5}, '20': {'diameter': 2.0, 'speed': 6000.0, 'start_radius': 2.0}, '30': {'diameter': 3.0, 'speed': 6000.0, 'start_radius': 3.0}}
        """
        self.tablewidget.blockSignals(True) # Avoid unnecessary signal (we don't want the config window to emit any signal when filling the fields programatically)
        result = True
        if isinstance(value, dict) and len(self.keys) > 0:
            self.tablewidget.setRowCount(0)
            line = [None] * len(self.keys)

            #sort according to the key
            item_list=[]
            try:
                #try numeric sort
                item_list = sorted(value.keys(), key=float)
            except ValueError:
                #fallback to standard sort
                item_list = sorted(value.keys())

            for item in item_list:
                line[0] = item #First column is alway the key of the dict (eg it can be the tool number)

                #Compute the other columns (the received value must contain a dict entry for each column)
                i = 1
                while i < len(self.keys):
                    if self.keys[i] in value[item]:
                        line[i] = value[item][self.keys[i]] #Get the value for a given column
                    else:
                        result = False
                        break
                    i += 1

                if result is True:
                    self.appendLine(line)
        else:
            result = False

        self.tablewidget.blockSignals(False)

        return result


class CfgTableCustomActions(CfgTable):
    """
    Subclassed CfgTableWidget to use muli-line edits for storing the custom GCODE.
    """

    def __init__(self, text, columns = None, parent = None):
        """
        Initialization of the CfgTableCustomActions class (editable 2D table for storing custom GCODE).
        @param text: text string associated with the table
        @param columns: string list containing all the columns names
        """
        CfgTable.__init__(self, text, columns, parent)

    def setCellValue(self, line, column, value):
        """
        This function is reimplemented to use QTextEdit into the table, thus allowing multi-lines custom GCODE to be stored
        @param line: line number (int)
        @param column: column number (int)
        @param value: cell content (string)
        """
        if column > 0:
            #Special case for column 1 : we use QTextEdit for storing the GCODE
            text_edit = QTextEdit()
            text_edit.setAcceptRichText(False)
            text_edit.setAutoFormatting(QTextEdit.AutoNone)
            text_edit.setPlainText(value)
            self.tablewidget.setCellWidget(line, column, text_edit)
            text_edit.textChanged.connect(self.valueChangedSlot) #We need to detect any change in the table's widgets
        else:
            #Normal case: use standard QT functions (and we dont need to generate any signal here, it is already handled by the parent class)
            CfgTable.setCellValue(self, line, column, value)

    def valueChangedSlot(self):
        """
        Slot called when something changes in the table. We emit a signal, so that the config window can detect this change
        """
        self.tableChanged.emit()

    def validateValue(self):
        """
        Check that the keys are unique and not empty
        @return (result_bool, result_string):
         - result_bool: True if no errors were encountered, False otherwise
         - result_string: a string containing all the errors encountered during the validation
        """
        #For now everything is OK
        result_string = ''
        result_bool = True
        keys_list = []

        if self.tablewidget.rowCount() > 0 and self.tablewidget.columnCount() > 0:
            for i in range(self.tablewidget.rowCount()):
                if not self.tablewidget.item(i, 0) or not self.tablewidget.item(i, 0).text():
                    result_bool = False
                    result_string += str(self.tr('\nThe cell at line {0}, column 0 must not be empty for the table "{1}"\n')).format(i, self.label.text())
                else:
                    #Create a list with all the "keys" from the first column (here a key is the custom action name)
                    keys_list.append(self.tablewidget.item(i, 0).text())

            nb_duplicate_elements = len(keys_list) - len(set(keys_list))
            if nb_duplicate_elements != 0:
                #There are duplicate entries, that's wrong because the key must be unique
                result_bool = False
                result_string += str(self.tr('\nFound {0} duplicate elements for the table "{1}"\n')).format(nb_duplicate_elements, self.label.text())

        return (result_bool, result_string)

    def getValue(self):
        """
        @return: a nested dictionnary that can be directly used to update the ConfigObj (class that handles configuration file)
        Example of returned value:
        {'pause': {'gcode': 'M5 (Spindle off)\nM9 (Coolant off)\nM0\n\nM8\nS5000M03 (Spindle 5000rpm cw)\n'}, 'probe_tool': {'gcode': '\nO<Probe_Tool> CALL\nS6000 M3 M8\n'}}
        """
        result_dict = {}
        #Get the keys (first column)
        for i in range(self.tablewidget.rowCount()):
            key = self.tablewidget.item(i, 0)
            if not key:
                continue
            key = str(key.text())
            if not key:
                continue
            result_dict[key] = {}

            #Get the values (other columns)
            for j in range(1, self.tablewidget.columnCount()):
                sub_key = self.keys[j] #Column name
                value = self.tablewidget.cellWidget(i, j)
                if not value:
                    continue
                value = str(value.toPlainText())
                if sub_key is not None:
                    result_dict[key][sub_key] = value

        return result_dict


class CfgTableToolParameters(CfgTable):
    """
    Subclassed CfgTableWidget to use muli-line edits for storing the custom GCODE.
    """

    def __init__(self, text, columns = None, parent = None):
        """
        Initialization of the CfgTableWidget class (editable 2D table for storing the tools table).
        @param text: text string associated with the table
        @param columns: string list containing all the columns names
        """
        self.max_tool_number = 0
        CfgTable.__init__(self, text, columns, parent)

    def setCellValue(self, line, column, value):
        """
        This function is reimplemented to use QTextEdit into the table, thus allowing multi-lines custom GCODE to be stored
        @param line: line number (int)
        @param column: column number (int)
        @param value: cell content (string or int or float)
        """
        if column > 0:
            #we use QDoubleSpinBox for storing the values
            spinbox = CorrectedDoubleSpinBox()
            spinbox.setMinimum(0)
            spinbox.setMaximum(1000000000) #Default value is 99
            computed_value = toFloat(value)[0]  # Convert the value to float
            spinbox.setValue(computed_value)
        else:
            #tool number is an integer
            spinbox = QSpinBox()
            spinbox.setMinimum(0)
            spinbox.setMaximum(1000000000) #Default value is 99

            converted_value = toInt(value)  # Convert the value to int (we may receive a string for example)
            computed_value = converted_value[0] if converted_value[1] else self.max_tool_number + 1
            self.max_tool_number = max(self.max_tool_number, computed_value) #Store the max value for the tool number, so that we can automatically increment this value for new tools
            spinbox.setValue(computed_value) #first column is the key, it must be an int

        spinbox.valueChanged.connect(self.valueChangedSlot) #We need to detect any change in the table's widgets

        self.tablewidget.setCellWidget(line, column, spinbox)

    def valueChangedSlot(self):
        """
        Slot called when something changes in the table. We emit a signal, so that the config window can detect this change
        """
        self.tableChanged.emit()

    def validateValue(self):
        """
        Check that the keys are unique and not empty
        @return (result_bool, result_string):
         - result_bool: True if no errors were encountered, False otherwise
         - result_string: a string containing all the errors encountered during the validation
        """
        #For now everything is OK
        contains_tool_1 = False
        result_string = ''
        result_bool = True
        keys_list = []

        if self.tablewidget.rowCount() > 0 and self.tablewidget.columnCount() > 0:
            for i in range(self.tablewidget.rowCount()):
                if not self.tablewidget.cellWidget(i, 0):
                    result_bool = False
                    result_string += str(self.tr('\nThe cell at line {0}, column 0 must not be empty for the table "{1}"\n')).format(i, self.label.text())
                else:
                    #Create a list with all the "keys" from the first column (here a key is the custom action name)
                    keys_list.append(str(self.tablewidget.cellWidget(i, 0).value()))
                    if self.tablewidget.cellWidget(i, 0).value() == 1:
                        contains_tool_1 = True

            nb_duplicate_elements = len(keys_list) - len(set(keys_list))
            if nb_duplicate_elements != 0:
                #There are duplicate entries, that's wrong because the key must be unique
                result_bool = False
                result_string += str(self.tr('\nFound {0} duplicate elements for the table "{1}"\n')).format(nb_duplicate_elements, self.label.text())

        if not contains_tool_1:
            result_bool = False
            result_string += str(self.tr('\nThe table "{0}" must always contains tool number \'1\'\n')).format(self.label.text()) #Note: str() is needed for PyQt4

        return (result_bool, result_string)

    def getValue(self):
        """
        @return: a nested dictionnary that can be directly used to update the ConfigObj (class that handles configuration file)
        Example of returned value:
        {'pause': {'gcode': 'M5 (Spindle off)\nM9 (Coolant off)\nM0\n\nM8\nS5000M03 (Spindle 5000rpm cw)\n'}, 'probe_tool': {'gcode': '\nO<Probe_Tool> CALL\nS6000 M3 M8\n'}}
        """
        result_dict = {}
        #Get the keys (first column)
        for i in range(self.tablewidget.rowCount()):
            key = self.tablewidget.cellWidget(i, 0)
            if not key:
                continue
            key = str(key.value())
            if not key:
                continue
            result_dict[key] = {}

            #Get the values (other columns)
            for j in range(1,self.tablewidget.columnCount()):
                sub_key = self.keys[j] #Column name
                value = self.tablewidget.cellWidget(i, j)
                if not value:
                    continue
                value = value.value()
                if sub_key is not None:
                    result_dict[key][sub_key] = value

        return result_dict
