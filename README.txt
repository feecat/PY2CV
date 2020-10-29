# PY2CV - Python Opencv Industrial Vision

Industrial Machine Vision Based on Python and OpenCV, The QT Frame Based On DXF2GCODE. The Target is same as In-Sight Explorer

![](https://github.com/feecat/DOC/IMAGE/Example_1.gif)

## Origin

Industrial Machine Vision System is TOO EXPENSIVE. (Cognex\Keyence\Omron\...etc)

## Usage

1. Download Release Package
2. Unzip and run

## Function

1. Open Local jpg/bmp/png or Project File to ready process.
2. Open Local or Remote Camera
3. Add Some base opencv function
4. Support TCP Trigger and Data Return ( Not Complete yet)

## Develop

The Framework base on DXF2GCODE, I Modify it and i think its advanced.
I'm suggessting use vscode to develop this Repositories.
Package List:
PyQt5
pyqt5-tools
cx-Freeze
opencv-python
numpy
configobj

Use make_ui_tr.bat to generate ui and translate file.
Use make_cxfreeze_exe.bat to generate release package. (After finish, I'm Suggest manually delete unused package to reduce size) 

## Acknowledgement

Thanks DXF2GCODE Again.