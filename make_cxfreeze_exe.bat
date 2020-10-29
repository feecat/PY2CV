cxfreeze py2cv.py --base-name=win32gui --icon="images/opencv.ico"
echo d | xcopy .config dist\.config /S /Y
echo d | xcopy locales dist\locales /S /Y
pause