# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'form.ui'
#
# Created by: PyQt5 UI code generator 5.15.7
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


import sys
import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets

mode = 0 # 0 -> percentiles, 1 -> photon counts
i1 = 4
i2 = 100
i3 = 200

def va2col(lower, upper, v1, v2, v3):
    c1 = 0
    c2 = 0
    c3 = 0
    global mode
    if mode == 1: # photon counts
        if v1 < lower:
            c1 = 0
        elif v1 > upper:
            c1 = 255
        else:
            c1 = int((v1 - lower)/(upper - lower) * 255)
        if v2 < lower:
            c2 = 0
        elif v2 > upper:
            c2 = 255
        else:
            c2 = int((v2 - lower)/(upper - lower) * 255)
        if v3 < lower:
            c3 = 0
        elif v3 > upper:
            c3 = 255
        else:
            c3 = int((v3 - lower)/(upper - lower) * 255)
    elif mode == 0: # percentiles
        l = np.array((0,0,0))
        vamax = np.argmax(np.array((v1,v2,v3)))
        l[vamax] = 1
        vamin = np.argmin(np.array((v1,v2,v3)))
        l[vamin] = 1
        vamed = int(np.where(l == 0)[0])
        
        if vamax == 0:
            c1 = 255
        elif vamax == 1:
            c2 = 255
        else:
            c3 = 255
            
        if vamin == 0:
            c1 = 0
        elif vamin == 1:
            c2 = 0
        else:
            c3 = 0
            
        if vamed == 0:
            if vamax == 1:
                p = (v1 - v3)/(v2 - v3) * 100
            elif vamax == 2:
                p = (v1 - v2)/(v3 - v2) * 100
            c1 = int((p - lower)/(upper - lower) * 255)
        elif vamed == 1:
            if vamax == 0:
                p = (v2 - v3)/(v1 - v3) * 100
            elif vamax == 2:
                p = (v2 - v1)/(v3 - v1) * 100
            c2 = int((p - lower)/(upper - lower) * 255)
        elif vamed == 2:
            if vamax == 0:
                p = (v3 - v2)/(v1 - v2) * 100
            elif vamax == 1:
                p = (v3 - v1)/(v2 - v1) * 100
            c3 = int((p - lower)/(upper - lower) * 255)
            
    return c1, c2, c3
        
        

class Ui_ONI(object):
    def setupUi(self, ONI):
        ONI.setObjectName("ONI")
        ONI.resize(260, 261)
        self.label = QtWidgets.QLabel(ONI)
        self.label.setGeometry(QtCore.QRect(10, 0, 251, 31))
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        self.label.setFont(font)
        self.label.setObjectName("label")
        self.frame = QtWidgets.QFrame(ONI)
        self.frame.setGeometry(QtCore.QRect(9, 30, 241, 221))
        self.frame.setStyleSheet("border-color: rgb(135, 135, 135);\n"
"border-width : 1.2px;\n"
"border-style:inset;")
        self.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame.setObjectName("frame")
        self.photon_counts = QtWidgets.QRadioButton(self.frame)
        self.photon_counts.setGeometry(QtCore.QRect(120, 10, 101, 22))
        self.photon_counts.setObjectName("photon_counts")
        self.percentiles = QtWidgets.QRadioButton(self.frame)
        self.percentiles.setGeometry(QtCore.QRect(20, 10, 91, 22))
        self.percentiles.setChecked(True)
        self.percentiles.setObjectName("percentiles")
        self.label_3 = QtWidgets.QLabel(self.frame)
        self.label_3.setGeometry(QtCore.QRect(20, 50, 43, 25))
        self.label_3.setObjectName("label_3")
        self.label_4 = QtWidgets.QLabel(self.frame)
        self.label_4.setGeometry(QtCore.QRect(20, 80, 49, 25))
        self.label_4.setObjectName("label_4")
        self.lower1 = QtWidgets.QDoubleSpinBox(self.frame)
        self.lower1.setGeometry(QtCore.QRect(100, 50, 62, 25))
        self.lower1.setMaximum(100.0)
        self.lower1.setSingleStep(0.1)
        self.lower1.setProperty("value", 5.0)
        self.lower1.setObjectName("lower1")
        self.label_2 = QtWidgets.QLabel(self.frame)
        self.label_2.setGeometry(QtCore.QRect(20, 120, 91, 25))
        self.label_2.setObjectName("label_2")
        self.upper1 = QtWidgets.QDoubleSpinBox(self.frame)
        self.upper1.setGeometry(QtCore.QRect(100, 80, 62, 25))
        self.upper1.setMaximum(100.0)
        self.upper1.setSingleStep(0.1)
        self.upper1.setProperty("value", 99.99)
        self.upper1.setObjectName("upper1")
        self.lower2 = QtWidgets.QDoubleSpinBox(self.frame)
        self.lower2.setGeometry(QtCore.QRect(160, 50, 62, 25))
        self.lower2.setMaximum(100.0)
        self.lower2.setSingleStep(0.1)
        self.lower2.setProperty("value", 5.0)
        self.lower2.setObjectName("lower2")
        self.upper2 = QtWidgets.QDoubleSpinBox(self.frame)
        self.upper2.setGeometry(QtCore.QRect(160, 80, 62, 25))
        self.upper2.setMaximum(100.0)
        self.upper2.setSingleStep(0.1)
        self.upper2.setProperty("value", 99.99)
        self.upper2.setObjectName("upper2")
        self.intensity1 = QtWidgets.QSpinBox(self.frame)
        self.intensity1.setGeometry(QtCore.QRect(20, 150, 61, 25))
        self.intensity1.setMinimum(1)
        self.intensity1.setMaximum(10000)
        self.intensity1.setProperty("value", i1)
        self.intensity1.setObjectName("intensity1")
        self.intensity2 = QtWidgets.QSpinBox(self.frame)
        self.intensity2.setGeometry(QtCore.QRect(80, 150, 61, 25))
        self.intensity2.setMinimum(1)
        self.intensity2.setMaximum(10000)
        self.intensity2.setProperty("value", i2)
        self.intensity2.setObjectName("intensity2")
        self.intensity3 = QtWidgets.QSpinBox(self.frame)
        self.intensity3.setGeometry(QtCore.QRect(140, 150, 61, 25))
        self.intensity3.setMinimum(1)
        self.intensity3.setMaximum(10000)
        self.intensity3.setProperty("value", i3)
        self.intensity3.setObjectName("intensity3")
        self.bead1 = QtWidgets.QLabel(self.frame)
        self.bead1.setGeometry(QtCore.QRect(20, 180, 61, 25))
        self.bead1.setStyleSheet("background-color:rgb(0, 0, 0);")
        self.bead1.setText("")
        self.bead1.setObjectName("bead1")
        self.bead2 = QtWidgets.QLabel(self.frame)
        self.bead2.setGeometry(QtCore.QRect(80, 180, 61, 25))
        self.bead2.setStyleSheet("background-color:rgb(118, 118, 118);")
        self.bead2.setText("")
        self.bead2.setObjectName("bead2")
        self.bead3 = QtWidgets.QLabel(self.frame)
        self.bead3.setGeometry(QtCore.QRect(140, 180, 61, 25))
        self.bead3.setStyleSheet("background-color:rgb(255, 255, 255);")
        self.bead3.setText("")
        self.bead3.setObjectName("bead3")
        self.frame.raise_()
        self.label.raise_()

        self.retranslateUi(ONI)
        QtCore.QMetaObject.connectSlotsByName(ONI)
        
        # connect signals to slots
        self.lower1.editingFinished.connect(self.setlower1)
        self.upper1.editingFinished.connect(self.setupper1)
        self.upper2.editingFinished.connect(self.setupper2)
        self.intensity1.valueChanged.connect(self.setintensity1)
        self.intensity2.valueChanged.connect(self.setintensity2)
        self.intensity3.valueChanged.connect(self.setintensity3)
        self.percentiles.clicked.connect(self.set2percentiles)
        self.photon_counts.clicked.connect(self.set2photoncount)

    def retranslateUi(self, ONI):
        _translate = QtCore.QCoreApplication.translate
        ONI.setWindowTitle(_translate("ONI", "ONI"))
        self.label.setText(_translate("ONI", "IMAGE DISPLAY OPTIONS"))
        self.photon_counts.setText(_translate("ONI", "Photon counts"))
        self.percentiles.setText(_translate("ONI", "Pencentiles"))
        self.label_3.setText(_translate("ONI", "Lower:"))
        self.label_4.setText(_translate("ONI", "Upper:"))
        self.label_2.setText(_translate("ONI", "Intensity (a.u.):"))
        
        
    def flush(self):
        c1, c2, c3 = va2col(self.lower1.value(), self.upper1.value(), self.intensity1.value(), self.intensity2.value(), self.intensity3.value())
        ss1 =  "background-color:rgb(" + str(c1) + ", " + str(c1) + ", " + str(c1) + ");"
        ss2 =  "background-color:rgb(" + str(c2) + ", " + str(c2) + ", " + str(c2) + ");"
        ss3 =  "background-color:rgb(" + str(c3) + ", " + str(c3) + ", " + str(c3) + ");"
        self.bead1.setStyleSheet(ss1)
        self.bead2.setStyleSheet(ss2)
        self.bead3.setStyleSheet(ss3)
    
    def setlower1(self):
        global mode
        v = self.lower1.value()
        
        if v >= self.upper1.value():
            if mode == 0:
                v = self.upper1.value() - 0.01
                self.lower1.setValue(v)
            else:
                v = self.upper1.value() - 1
                self.lower1.setValue(v)
        
        self.lower2.setValue(v)
        
        self.flush()
        
    def setlower2(self):
        global mode
        v = self.lower2.value()
        
        if v >= self.upper2.value():
            if mode == 0:
                v = self.upper2.value() - 0.01
                self.lower2.setValue(v)
            else:
                v = self.upper2.value() - 1
                self.lower2.setValue(v)
        
        self.lower1.setValue(v)
        
        self.flush()
        
    def setupper1(self):
        global mode
        v = self.upper1.value()
        
        if v <= self.lower1.value():
            if mode == 0:
                v = self.lower1.value() + 0.01
                self.upper1.setValue(v)
            else:
                v = self.lower1.value() + 1
                self.upper1.setValue(v)
        
        self.upper2.setValue(v)
        
        self.flush()
        
    def setupper2(self):
        global mode
        v = self.upper2.value()
        
        if v <= self.lower2.value():
            if mode == 0:
                v = self.lower2.value() + 0.01
                self.upper2.setValue(v)
            else:
                v = self.lower2.value() + 1
                self.upper2.setValue(v)
        
        self.upper1.setValue(v)
        
        self.flush()
    
    def setintensity1(self):
        self.flush()
        
    def setintensity2(self):
        self.flush()
        
    def setintensity3(self):
        self.flush()
        
    def set2percentiles(self):
        global mode
        mode = 0
        
        self.lower1.setDecimals(2)
        self.lower2.setDecimals(2)
        self.upper1.setDecimals(2)
        self.upper2.setDecimals(2)
        
        v = self.lower1.value()
        if v > 100.0:
            v = 5.0
        self.lower1.setValue(v)
        self.lower1.setMaximum(100.0)
        self.lower1.setSingleStep(0.1)
        v = self.lower2.value()
        if v > 100.0:
            v = 5.0
        self.lower2.setValue(v)
        self.lower2.setMaximum(100.0)
        self.lower2.setSingleStep(0.1)
        v = self.upper1.value()
        if v > 100.0:
            v = 100.0
        self.upper1.setValue(v)
        self.upper1.setMaximum(100.0)
        self.upper1.setSingleStep(0.1)
        v = self.upper2.value()
        if v > 100.0:
            v = 100.0
        self.upper2.setValue(v)
        self.upper2.setMaximum(100.0)
        self.upper2.setSingleStep(0.1)
        
        self.flush()
        
    def set2photoncount(self):
        global mode
        mode = 1
        
        self.lower1.setMaximum(10000)
        self.lower2.setMaximum(10000)
        self.upper1.setMaximum(10000)
        self.upper2.setMaximum(10000)
        
        self.lower1.setSingleStep(1)
        self.lower2.setSingleStep(1)
        self.upper1.setSingleStep(1)
        self.upper2.setSingleStep(1)
        
        v = self.lower1.value()
        self.lower1.setValue(int(v))
        v = self.lower2.value()
        self.lower2.setValue(int(v))
        v = self.upper1.value()
        self.upper1.setValue(int(v))
        v = self.upper2.value()
        self.upper2.setValue(int(v))
        
        self.lower1.setDecimals(0)
        self.lower2.setDecimals(0)
        self.upper1.setDecimals(0)
        self.upper2.setDecimals(0)
        
        self.flush()
        
        

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    ONI = QtWidgets.QMainWindow()
    ui = Ui_ONI()
    ui.setupUi(ONI)
    ONI.show()
    sys.exit(app.exec_())