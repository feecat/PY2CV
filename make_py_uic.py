#!/usr/bin/env python3

"""
Generates the python file based on the defined uifile
"""

import os
import subprocess
import sys
import tempfile

import py2cv.globals.constants as c


def which(program):
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None


pyQtVer = '5'

if "linux" in sys.platform.lower() or "unix" in sys.platform.lower() or "darwin" in sys.platform.lower():
    # On Linux and macOS executables are normaly on the PATH (on Linux please install packages like lib64-qt5-devel and python-qt5-devel)
    names = ["pyuic%s" % pyQtVer]
    UICPATH = None

    for name in names:
        if which(name):
            UICPATH = name
            break

    if not UICPATH:
        print("ERROR: Cannot file uic tool.")
        print("Please consider to install uic tool - to use this script.")
        sys.exit(1)

    names = ["pyrcc%s" % pyQtVer]
    RCCPATH = None

    for name in names:
        if which(name):
            RCCPATH = name
            break

    if not UICPATH:
        print("ERROR: Cannot file rcc tool.")
        print("Please consider to install rcc tool - to use this script.")
        sys.exit(1)

    RCCPATH = "pyrcc%s" % pyQtVer

    print("Using platform tools \"%s\" and \"%s\"\n" % (UICPATH, RCCPATH))
else:
    PYTHONPATH = os.path.split(sys.executable)[0]
    UICPATH = os.path.join(PYTHONPATH, "Scripts/pyuic5.exe")
    RCCPATH = os.path.join(PYTHONPATH, "Scripts/pyrcc5.exe")
    print("Using Windows platform tools \"%s\" and \"%s\"\n" % (UICPATH, RCCPATH))

FILEPATH = os.path.realpath(os.path.dirname(sys.argv[0]))

UIFILE = "py2cv.ui"
PYFILEver = "py2cv_ui%s.py" % pyQtVer

RCFILE = "py2cv_images.qrc"
RCFILEver = "py2cv_images%s.qrc" % pyQtVer

RCPYFILEver = "py2cv_images%s_rc.py" % pyQtVer

ui_data = ""
with open(UIFILE, "r",encoding='utf-8') as myfile:
    ui_data = myfile.read().replace(RCFILE, RCFILEver)

fd, tmp_ui_filename = tempfile.mkstemp()
try:
    os.write(fd, bytes(ui_data, 'UTF-8'))
    os.close(fd)

    OPTIONS = "-o"

    cmd1 = [UICPATH, tmp_ui_filename, OPTIONS, PYFILEver]
    cmd2 = [RCCPATH, OPTIONS, RCPYFILEver, RCFILE]

    print(" ".join(cmd1))
    subprocess.check_call(cmd1)

    print(" ".join(cmd2))
    subprocess.check_call(cmd2)

finally:
    os.remove(tmp_ui_filename)

print("Please consider to not commit any auto-generated files.")
print("\nREADY")
