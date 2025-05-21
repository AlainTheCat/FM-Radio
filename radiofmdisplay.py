#!/usr/bin/python3

"""
Wigdet Radio FM display

Author: Alain CUYNAT
Website: mao2.fr

"""

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QFont, QColor, QPen


class RadioFMDisplay(QWidget):

    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):

        self.setMinimumSize(1, 60)
        self.value = 880
        self.colorBackground = QColor(240, 240, 240)
        self.colorTrack = QColor(255, 64, 64)
        self.blue = 128
        self.green = 184
        self.num = []
        self.num = range(88, 110)

    def setValue(self, value):

        self.value = value

    def setColorBackground(self, color):
        self.colorBackground = color

    def paintEvent(self, e):

        qp = QPainter()
        qp.begin(self)
        self.drawWidget(qp)
        qp.end()

    def drawWidget(self, qp):

        font = QFont('Serif', 7, QFont.Light)
        qp.setFont(font)

        size = self.size()
        w = size.width()
        h = size.height()


        # qp.setBrush(Qt.NoBrush)
        qp.setBrush(self.colorBackground)
        qp.drawRect(0, 0, w - 1, h - 1)

        step = int(round(w / 22))
        till = int((step * (self.value/10 - 87)))

        qp.setPen(QColor(255, 255, 255))
        qp.setBrush(self.colorTrack)
        qp.drawRect(till-3, 0, 6, h)

        pen = QPen(QColor(20, 20, 184), 1,
                   Qt.SolidLine)
        qp.setPen(pen)

        j = 0

        for i in range(step, 22 * step, step):

            qp.drawLine(i, 0, i, 5)
            metrics = qp.fontMetrics()
            fw = metrics.horizontalAdvance(str(self.num[j]))

            x, y = int(i - fw/2), int(h / 2)
            qp.drawText(x, y, str(self.num[j]))
            j = j + 1
