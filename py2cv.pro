TARGET = py2cv.py

SOURCES += \
    py2cv.py \
    make_tr.py \
    py2cv.py \\
    make_py_uic.py \
    make_tr.py \\
    py2cv/__init__.py \
    py2cv/core/__init__.py \
    py2cv/core/point.py \
    py2cv/core/boundingbox.py \
    py2cv/core/breakgeo.py \
    py2cv/core/customgcode.py \
    py2cv/core/entitycontent.py \
    py2cv/core/layercontent.py \
    py2cv/core/linegeo.py \
    py2cv/core/project.py \
    py2cv/core/shape.py \
    py2cv/globals/__init__.py \
    py2cv/globals/config.py \
    py2cv/globals/constants.py \
    py2cv/globals/d2gexceptions.py \
    py2cv/globals/globals.py \
    py2cv/globals/helperfunctions.py \
    py2cv/globals/logger.py \
    py2cv/gui/__init__.py \
    py2cv/gui/aboutdialog.py \
    py2cv/gui/canvas.py \
    py2cv/gui/canvas2d.py \
    py2cv/gui/configwindow.py \
    py2cv/gui/messagebox.py \
    py2cv/gui/popupdialog.py \
    py2cv/gui/routetext.py \
    py2cv/gui/treehandling.py \
    py2cv/gui/treeview.py \
    py2cv/gui/wpzero.py \

DISTFILES += \
    README.txt \

RESOURCES += \
    py2cv_images.qrc

FORMS += \
    py2cv.ui

TRANSLATIONS += \
    locales/py2cv_de_DE.ts \
    locales/py2cv_fr.ts \
    locales/py2cv_ru.ts \
	locales/py2cv_zh_CN.ts
