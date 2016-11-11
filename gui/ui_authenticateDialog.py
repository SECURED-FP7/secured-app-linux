# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'authenticate.ui'
#
# Created: Wed Nov 11 13:02:28 2015
#      by: PyQt4 UI code generator 4.10.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_AuthenticateDialog(object):
    def setupUi(self, AuthenticateDialog):
        AuthenticateDialog.setObjectName(_fromUtf8("AuthenticateDialog"))
        AuthenticateDialog.resize(384, 150)
        self.verticalLayout = QtGui.QVBoxLayout(AuthenticateDialog)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.gridLayout = QtGui.QGridLayout()
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.label = QtGui.QLabel(AuthenticateDialog)
        self.label.setObjectName(_fromUtf8("label"))
        self.gridLayout.addWidget(self.label, 2, 0, 1, 1)
        self.lineEdit_user = QtGui.QLineEdit(AuthenticateDialog)
        self.lineEdit_user.setObjectName(_fromUtf8("lineEdit_user"))
        self.gridLayout.addWidget(self.lineEdit_user, 2, 1, 1, 1)
        self.label_2 = QtGui.QLabel(AuthenticateDialog)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.gridLayout.addWidget(self.label_2, 3, 0, 1, 1)
        self.lineEdit_passwd = QtGui.QLineEdit(AuthenticateDialog)
        self.lineEdit_passwd.setEchoMode(QtGui.QLineEdit.Password)
        self.lineEdit_passwd.setObjectName(_fromUtf8("lineEdit_passwd"))
        self.gridLayout.addWidget(self.lineEdit_passwd, 3, 1, 1, 1)
        self.verticalLayout.addLayout(self.gridLayout)
        spacerItem1 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem1)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setContentsMargins(0, -1, -1, -1)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        spacerItem2 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem2)
        self.okButton = QtGui.QPushButton(AuthenticateDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.okButton.sizePolicy().hasHeightForWidth())
        self.okButton.setSizePolicy(sizePolicy)
        self.okButton.setMinimumSize(QtCore.QSize(150, 0))
        self.okButton.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.okButton.setObjectName(_fromUtf8("okButton"))
        self.horizontalLayout.addWidget(self.okButton)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.label.setBuddy(self.lineEdit_user)
        self.label_2.setBuddy(self.lineEdit_passwd)

        self.retranslateUi(AuthenticateDialog)
        QtCore.QObject.connect(self.okButton, QtCore.SIGNAL(_fromUtf8("clicked()")), AuthenticateDialog.accept)
        QtCore.QMetaObject.connectSlotsByName(AuthenticateDialog)

    def retranslateUi(self, AuthenticateDialog):
        AuthenticateDialog.setWindowTitle(_translate("AuthenticateDialog", "SECURED authentication", None))
        self.label.setText(_translate("AuthenticateDialog", "Username:", None))
        self.label_2.setText(_translate("AuthenticateDialog", "Password:", None))
        self.okButton.setText(_translate("AuthenticateDialog", "Login", None))

