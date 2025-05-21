#!/usr/bin/python3
# This Python file uses the following encoding: utf-8
# -*- coding: utf-8 -*-
"""
 FM Radio receiver on USB HID

 This is a control panel of FM radio receiver  with RDS information
 This program is build with Python 3, PySide6 and QtDesigner
 The device is plugged on USB HID
 For installation read readme.txt file

 Author: Alain Cuynat
 Website: mao2.fr
"""

import sys
import hid
import json
import math
from MainWindow import Ui_MainWindow
from PySide6.QtWidgets import QMainWindow, QMessageBox, QProgressBar
from PySide6.QtWidgets import QLabel, QPushButton
from PySide6.QtWidgets import QApplication, QVBoxLayout
from PySide6.QtCore import QTimer, QObject, Signal
from PySide6.QtGui import QIcon, QColor
from qled import QLed
from radiofmdisplay import RadioFMDisplay


class Communicate(QObject):
    updateDisplay = Signal(int)


class Radio:
    """
        Radio station
        ...
    Attributes:
        channel: float, channel frequency
        enable: bool, if true this channel is enabled
        id: int, radio ident
        name: string, name of this radio
    """

    def __init__(self, channel, enable, id, name):
        """ initializes Radio class """
        self.channel = channel
        self.enable = enable
        self.id = id
        self.name = name


# Creating list of radios
radios = []

# List all favorite radios
with open("radioSettings.json") as f:
    data1 = json.load(f)

# Appending instances to list
for i in range(16):
    radios.append(
        Radio(
            data1["preset" + str(i)]["channel"],
            data1["preset" + str(i)]["enable"],
            data1["preset" + str(i)]["id"],
            data1["preset" + str(i)]["name"],
        )
    )


class Fm(QMainWindow, Ui_MainWindow):
    """Radio panel (creating and playing)"""

    def __init__(self):
        """Initializes the MainWindow class"""
        super().__init__()

        self.setupUi(self)
        self.setWindowIcon(QIcon("radio.png"))
        self.setWindowTitle("RADIO FM")

        self.initVariables()
        self.initDevice()
        self.createConnections()

        self.led = QLed()
        self.layoutPower.insertWidget(0, self.led)

        self.com = Communicate()
        self.radioDisplay = RadioFMDisplay()
        self.layoutRadioDisplay.addWidget(self.radioDisplay)
        self.radioDisplay.setValue(896)
        self.com.updateDisplay[int].connect(self.radioDisplay.setValue)

        self.timer = QTimer()


    def initVariables(self):
        """Initializes variables

        """

        # Read and write buffers
        # IN -> Read from the Device
        # Received data will be stored here - the first byte in the array is unused
        bufferInSize = 40                       # Size of the data buffer coming IN to the PC
        self.bufferIn = [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                         0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                         0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
        # OUT -> Write to the device
        # Transmitted data is stored here - the first item in the array must be 0
        bufferOutSize = 16                      # Size of the data buffer going OUT from the PC
        self.bufferOut = [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]

        self.hidToSend = False

        DLS_Ascii = (32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32,
                     32, 32, 32, 32, 32, 32, 32, 32, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47,
                     48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71,
                     72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95,
                     96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115,
                     116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 32, 225, 224, 233, 232, 237, 236, 243,
                     242, 250, 249, 209, 199, 32, 223, 161, 32, 226, 228, 234, 235, 238, 239, 244, 246, 251, 252, 241,
                     231, 32, 32, 32, 32, 170, 32, 169, 137, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 186, 185,
                     178, 179, 177, 32, 32, 32, 181, 191, 247, 176, 188, 189, 190, 167, 193, 192, 201, 200, 205, 204,
                     211, 210, 218, 217, 32, 32, 154, 142, 208, 32, 194, 196, 202, 203, 206, 207, 212, 214, 219, 220,
                     32, 32, 32, 158, 32, 32, 32, 197, 198, 140, 32, 253, 213, 216, 254, 32, 32, 32, 32, 32, 32, 32,
                     227, 229, 230, 156, 32, 253, 245, 248, 32, 32, 32, 32, 32, 32, 32, 32)

        self.comboBoxDeEmphasis.addItems(["USA 75 µSec", "Europe 50 µSec", "Disabled"])
        self.comboBoxDeEmphasis.setCurrentText("Europe 50 µSec")

        self.spinBoxUpDownSeekThreshold.setValue(17)

        self.RTA = []
        self.RTB = []
        for rta in range(16):
            self.RTA.append("    ")
            self.RTB.append("    ")
        self.PS = ["    ", "    ", "    ", "    "]

        self.pushButtonOn.setEnabled(True)
        self.pushButtonOff.setEnabled(False)
        self.clearPanel()
        self.clearTextBox()

        self.toolStripStatusLabel1.setText("FM Tuner not connected")
        self.toolStripStatusLabel2.setText("")
        self.toolStripStatusLabel3.setText("")
        self.toolStripStatusLabel4.setText("")

    def initDevice(self):
        """init the device"""
        self.myDevice = self.checkDevice()
        # print(self.myDevice)

    def checkDevice(self):
        """Check the device"""
        VENDOR_ID = 0x1234
        PRODUCT_ID = 0x4684
        try:
            device = hid.Device(vid=VENDOR_ID, pid=PRODUCT_ID)
            return device
        except Exception:
            try:
                res = hid.enumerate(vid=VENDOR_ID, pid=PRODUCT_ID)
                dict1 = res[0]
                hidPath = dict1["path"].decode()
                print("sudo chmod 0666 " + hidPath)
                msgBox1 = QMessageBox()
                msgBox1.setWindowTitle("DEVICE ERROR")
                msgBox1.setText("Device can't open")
                msgBox1.setInformativeText("sudo chmod 0666 " + hidPath)
                msgBox1.setStandardButtons(QMessageBox.StandardButton.Ok)
                if msgBox1.exec() == QMessageBox.StandardButton.Ok:
                    exit()
                else:
                    pass

            except Exception:
                msgBox2 = QMessageBox()
                msgBox2.setWindowTitle("DEVICE ERROR")
                msgBox2.setText("Device no found")
                msgBox2.setInformativeText("Plug your device !")
                msgBox2.setStandardButtons(QMessageBox.StandardButton.Ok)
                if msgBox2.exec() == QMessageBox.StandardButton.Ok:
                    exit()
                else:
                    pass

    def close(self):
        """Stand by the device"""
        self.bufferOut[0] = 0x00
        self.bufferOut[1] = 0x00
        dataOut = self.buffertostring(self.bufferOut)
        self.lineEditBufferOut.setText(dataOut)
        order = bytes(bytearray(self.bufferOut))
        self.hidSend(order)
        self.clearPanel()
        self.clearTextBox()
        self.toolStripStatusLabel1.setText("FM Tuner Disconnected")
        self.toolStripStatusLabel2.setText("")
        self.toolStripStatusLabel3.setText("")
        self.toolStripStatusLabel4.setText("")

        self.led.toggleValue()

        self.radioDisplay.setColorBackground(QColor(240, 240, 240))


    def clearPanel(self):
        """
        Clear this panel
        :return:
        """
        self.pushButtonOn.setEnabled(True)
        self.pushButtonOff.setEnabled(False)
        self.labelRSSI.setText("0 dbµV")
        self.labelSNR.setText("0 dB")
        self.labelMultipath.setText("0")
        self.labelFrequencyOff.setText("0 PPM")
        self.labelHighCut.setText("KHz")
        self.labelSoftMute.setText("0 dB")
        self.labelStereoBlend.setText("0 %")
        self.pushButtonSeekDown.setEnabled(False)
        self.pushButtonSeekUp.setEnabled(False)
        self.pushButtonTuneDown.setEnabled(False)
        self.pushButtonTuneUp.setEnabled(False)
        self.pushButtonPreset1.setEnabled(False)
        self.pushButtonPreset2.setEnabled(False)
        self.pushButtonPreset3.setEnabled(False)
        self.pushButtonPreset4.setEnabled(False)
        self.pushButtonPreset5.setEnabled(False)
        self.pushButtonPreset6.setEnabled(False)
        self.pushButtonPreset7.setEnabled(False)
        self.pushButtonPreset8.setEnabled(False)
        self.pushButtonPreset9.setEnabled(False)
        self.pushButtonPreset10.setEnabled(False)
        self.pushButtonPreset11.setEnabled(False)
        self.pushButtonPreset12.setEnabled(False)
        self.pushButtonPreset13.setEnabled(False)
        self.pushButtonPreset14.setEnabled(False)
        self.pushButtonPreset15.setEnabled(False)
        self.pushButtonPreset16.setEnabled(False)
        self.checkBoxMono.setEnabled(False)
        self.checkBoxMute.setEnabled(False)
        self.checkBoxMemory.setEnabled(False)
        self.comboBoxDeEmphasis.setEnabled(False)
        self.spinBoxUpDownSeekThreshold.setEnabled(False)
        self.horizontalScrollBarVolume.setEnabled(False)

    def clearTextBox(self):
        """ Clear all TextBox (lineEdit)"""
        self.lineEditDI.setText("")
        self.lineEditPS.setText("")
        self.lineEditFrequencyValue.setText("")
        self.lineEditFrequency.setText("")
        self.lineEditCompressed.setText("")
        self.lineEditDate.setText("")
        self.lineEditHead.setText("")
        self.lineEditMJD.setText("")
        self.lineEditPID.setText("")
        self.lineEditPTY.setText("")
        self.lineEditTextA.setText("")
        self.lineEditTextB.setText("")
        self.lineEditProgramType.setText("")
        self.lineEditStereo.setText("")
        self.lineEditTime.setText("")


    def open(self):
        """a HID device has been plugged in..."""
        # loadServices()
        self.bufferOut[0] = 0x00
        self.bufferOut[1] = 0x01
        self.bufferOut[2] = 0x01
        self.bufferOut[3] = 0x00
        self.bufferOut[4] = 0x23
        self.bufferOut[5] = 0x00
        self.bufferOut[6] = 0x00
        self.bufferOut[7] = 0x00
        self.bufferOut[8] = 0x00
        self.bufferOut[9] = 0x00
        self.bufferOut[10] = 0x00
        self.bufferOut[11] = 0x00
        self.bufferOut[12] = 0x00
        self.bufferOut[13] = 0x63
        self.bufferOut[14] = 0x11
        self.bufferOut[15] = 0x00
        dataOut = self.buffertostring(self.bufferOut)
        self.lineEditBufferOut.setText(dataOut)
        order = bytes(bytearray(self.bufferOut))
        self.hidSend(order)
        self.timer.timeout.connect(self.readDevice)
        self.timer.start(50)
        self.pushButtonOn.setEnabled(False)
        self.pushButtonOff.setEnabled(True)
        self.toolStripStatusLabel1.setText("FM Tuner connected")
        self.toolStripStatusLabel2.setText("")
        self.toolStripStatusLabel3.setText("")
        self.toolStripStatusLabel4.setText("")

        self.loadSettingsIni()

        self.led.toggleValue()

        self.radioDisplay.setColorBackground(QColor(210, 255, 210))


    def bytetostring(self, data):
        """Converts a Byte in data to String in hexadecimal form

        Args:
            data: Byte, for example b'\x00\x01\x15\x14\x8d'

        Returns:
            dataStr: String like this "00 01 15 14 8d"
        """
        dataStr = ""
        for i in data:
            dataStr = dataStr + " " + hex(i)
        dataStr = dataStr.replace("0x", "")
        return dataStr

    def buffertostring(self, buffer):
        """Converts a list of value  in data to String in hexadecimal form

                Args:
                    data: List eg. buffer = [0x00, 0x01, 0x15, 0x14, 0x8d]

                Returns:
                    dataStr: String like this "00 00 01 15 14 8d"
        """
        dataStr = ""
        for i in buffer:
            dataStr = dataStr + " " + hex(i)
        dataStr = dataStr.replace("0x", "")
        return dataStr

    def createConnections(self):
        """Identifies the different widgets and
        creates the necessary connections"""
        self.pushButtonOn.clicked.connect(self.open)
        self.pushButtonOff.clicked.connect(self.close)
        self.pushButtonPreset1.clicked.connect(lambda: self.buttonPresetPressed(0))
        self.pushButtonPreset2.clicked.connect(lambda: self.buttonPresetPressed(1))
        self.pushButtonPreset3.clicked.connect(lambda: self.buttonPresetPressed(2))
        self.pushButtonPreset4.clicked.connect(lambda: self.buttonPresetPressed(3))
        self.pushButtonPreset5.clicked.connect(lambda: self.buttonPresetPressed(4))
        self.pushButtonPreset6.clicked.connect(lambda: self.buttonPresetPressed(5))
        self.pushButtonPreset7.clicked.connect(lambda: self.buttonPresetPressed(6))
        self.pushButtonPreset8.clicked.connect(lambda: self.buttonPresetPressed(7))
        self.pushButtonPreset9.clicked.connect(lambda: self.buttonPresetPressed(8))
        self.pushButtonPreset10.clicked.connect(lambda: self.buttonPresetPressed(9))
        self.pushButtonPreset11.clicked.connect(lambda: self.buttonPresetPressed(10))
        self.pushButtonPreset12.clicked.connect(lambda: self.buttonPresetPressed(11))
        self.pushButtonSave.clicked.connect(self.saveSettings)
        self.horizontalScrollBarVolume.valueChanged.connect(self.horizontalScrollBarVolumeChanged)
        self.pushButtonSeekUp.clicked.connect(self.seekUpButtonPressed)
        self.pushButtonSeekDown.clicked.connect(self.seekDownButtonPressed)
        self.pushButtonTuneUp.clicked.connect(self.tuneUpButtonPressed)
        self.pushButtonTuneDown.clicked.connect(self.tuneDownButtonPressed)
        self.checkBoxMono.clicked.connect(self.checkBoxMonoClicked)
        self.checkBoxMute.clicked.connect(self.checkBoxMuteClicked)
        self.lineEditFrequencyValue.textChanged.connect(self.changeValue)
        self.checkBoxMemory.stateChanged.connect(self.enablePresetsSelected)


    def readDevice(self):
        """Reads the device"""
        # print("Device reading ...")
        try:
            self.bufferIn = self.myDevice.read(size=40, timeout=1)
            if self.bufferIn:
                dataInHex = self.buffertostring(self.bufferIn)
                self.lineEditBufferIn.setText(dataInHex)
                self.onRead()

        except Exception:
            pass
            """
            msgBox = QMessageBox()
            msgBox.setWindowTitle("Message")
            msgBox.setText("Reading error")
            msgBox.setStandardButtons(QMessageBox.StandardButton.Cancel)
            msgBox.setDefaultButton(QMessageBox.StandardButton.Cancel)
            answer = msgBox.exec()
            if answer == QMessageBox.StandardButton.Cancel:
                pass
            """

    def onRead(self):
        """On read event
        read the data (don't forget, pass the whole array)...
        """
        # self.timer3.setInterval(50)   # Disable HID_Send for 50 mSec
        match self.bufferIn[0]:
            case 0x08:                # Response 0x08 GET_PART_INFO ( See AN649 )
                self.partInfo()
            case 0x09:               # Response 0x09 GET_SYS_STATE ( See AN649 )
                self.systemState()
            case 0x12:               # Response 0x12 GET_FUNC_INFO ( See AN649 )
                self.firmwareRevision()
            case 0x32:               #
                self.fmRsqStatus()
            case 0x33:               #
                self.fmAcfStatus()
            case 0x34:               #
                self.fmRdsStatus()

    def partInfo(self):
        """
        Part Info
        """
        print("Part Info")
        Skyworks_Part_Number = str(self.bufferIn[13] * 256 + self.bufferIn[12])
        Microchip_Part_Number = chr(self.bufferIn[27]) + chr(self.bufferIn[28]) + chr(self.bufferIn[29]) + \
                                chr(self.bufferIn[30]) + chr(self.bufferIn[31]) + chr(self.bufferIn[32]) + \
                                chr(self.bufferIn[33]) + chr(self.bufferIn[34]) + chr(self.bufferIn[35]) + \
                                chr(self.bufferIn[36]) + chr(self.bufferIn[37]) + chr(self.bufferIn[38])
        partInfoText = Microchip_Part_Number + " / Si" + Skyworks_Part_Number
        self.toolStripStatusLabel2.setText(partInfoText)

    def systemState(self):
        """

        :return:

        """

        print("System State")
        Image_System = self.bufferIn[8]
        print(Image_System)
        match Image_System:
            case 0:
                self.toolStripStatusLabel3.setText("Bootloader is active")
            case 1:
                self.toolStripStatusLabel3.setText("FMHD is active")

                self.pushButtonSeekDown.setEnabled(True)
                self.pushButtonSeekUp.setEnabled(True)
                self.pushButtonTuneDown.setEnabled(True)
                self.pushButtonTuneUp.setEnabled(True)
                self.pushButtonPreset1.setEnabled(True)
                self.pushButtonPreset2.setEnabled(True)
                self.pushButtonPreset3.setEnabled(True)
                self.pushButtonPreset4.setEnabled(True)
                self.pushButtonPreset5.setEnabled(True)
                self.pushButtonPreset6.setEnabled(True)
                self.pushButtonPreset7.setEnabled(True)
                self.pushButtonPreset8.setEnabled(True)
                self.pushButtonPreset9.setEnabled(True)
                self.pushButtonPreset10.setEnabled(True)
                self.pushButtonPreset11.setEnabled(True)
                self.pushButtonPreset12.setEnabled(True)
                self.pushButtonPreset13.setEnabled(True)
                self.pushButtonPreset14.setEnabled(True)
                self.pushButtonPreset15.setEnabled(True)
                self.pushButtonPreset16.setEnabled(True)
                self.checkBoxMute.setEnabled(True)
                self.checkBoxMono.setEnabled(True)
                self.checkBoxMemory.setEnabled(True)
                self.comboBoxDeEmphasis.setEnabled(True)
                self.spinBoxUpDownSeekThreshold.setEnabled(True)
                self.horizontalScrollBarVolume.setEnabled(True)

            case 2:
                self.toolStripStatusLabel3.setText("DAB is active")
            case 3:
                self.toolStripStatusLabel3.setText("TDMB or data only DAB image is active")
            case 4:
                self.toolStripStatusLabel3.setText("FMHD Demod is active")
            case 5:
                self.toolStripStatusLabel3.setText("AMHD is active")
            case 6:
                self.toolStripStatusLabel3.setText("AMHD Demod is active")
            case 7:
                self.toolStripStatusLabel3.setText("FMHD is active")
            case 9:
                self.toolStripStatusLabel3.setText("DAB Demod is active")



    def firmwareRevision(self):
        """
        Give SI firmware and PIC firmware
        """
        print("firmware")

        SI_First_Rev = str(self.bufferIn[8])
        SI_Second_Rev = str(self.bufferIn[9])
        SI_Third_Rev = str(self.bufferIn[10])
        PIC_First_Rev = str(self.bufferIn[16])
        PIC_Second_Rev = str(self.bufferIn[17])
        PIC_Third_Rev = str(self.bufferIn[18])
        firmwareText = " PIC Firmware revision : " + PIC_First_Rev + "." + PIC_Second_Rev + "." + PIC_Third_Rev + \
                       " / Si Firmware revision : " + SI_First_Rev + "." + SI_Second_Rev + "." + SI_Third_Rev
        self.toolStripStatusLabel4.setText(firmwareText)

    def fmRsqStatus(self):
        readChannel = (self.bufferIn[11] * 256) + self.bufferIn[10]
        if (self.bufferIn[12] < 128):
            frequencyOffset = self.bufferIn[12]
        else:
            frequencyOffset = self.bufferIn[12] - 256
        if (self.bufferIn[13] < 128):
            RSSI = self.bufferIn[13]
        else:
           RSSI = self.bufferIn[13] - 256
        if (self.bufferIn[14] < 128):
            SNR =self.bufferIn[14]
        else:
            SNR = self.bufferIn[14] - 256
        multipath = self.bufferIn[15]
        self.lineEditFrequency.setText(str(readChannel/100) + " Mhz")
        self.lineEditFrequencyValue.setText(str(readChannel))
        self.labelFrequencyOff.setText(str(frequencyOffset) + " BPPM")
        self.labelRSSI.setText(str(RSSI) + " dBµV")
        self.labelSNR.setText(str(SNR) + " dB")
        self.labelMultipath.setText(str(multipath))
        self.progressBarFrequencyOffset.setValue(abs(frequencyOffset))
        self.progressBarRSSI.setValue(RSSI + 128)
        self.progressBarSNR.setValue(SNR + 128)
        self.progressBarMultipath.setvalue(multipath)

    def fmAcfStatus(self):
        softMuteattenuation = self.bufferIn[10]
        highCut = self.bufferIn[11]
        stereoBlend = self.bufferIn[12]
        self.labelSoftMute.setText(str(softMuteattenuation & 0x1F) + " dB")
        self.progressBarSoftMute.setValue(softMuteattenuation & 0x1F)
        self.labelHighCut.setText(str(highCut / 10) + " Khz")
        self.progressBarHighCut.setValue(highCut / 10)
        monoStereo = stereoBlend & 0x80
        if (monoStereo == 0x80):
            self.label4.setText("ST Blend")
            self.progressBarStBlend.setEnabled(True)
            self.labelStereoBlend.setText(str(stereoBlend & 0x7F) + " %")
            self.progressBarStBlend.setValue(stereoBlend & 0x7F)
        else:
            self.label4.setText(" Mono")
            self.labelStereoBlend.setText("")
            self.progressBarStBlend.setValue(0)
            self.progressBarStBlend.setEnabled(False)



    def fmRdsStatus(self):
        RDSA_L = self.bufferIn[16]
        RDSA_H = self.bufferIn[17]
        RDSB_L = self.bufferIn[18]
        RDSB_H = self.bufferIn[19]
        RDSC_L = self.bufferIn[20]
        RDSC_H = self.bufferIn[21]
        RDSD_L = self.bufferIn[22]
        RDSD_H = self.bufferIn[23]

        # Program Identification
        progID = str(RDSA_H) + str(RDSA_L)
        # print("Programme Identification : " + progID)
        self.lineEditPID.setText(progID)

        # Program Type
        pty = ((RDSB_H & 0x3) << 8) + ((RDSB_L & 0xE0) >> 32)
        # print("pty : " + str(pty))

        t0 = "00 No program type"
        t1 = "01 News()"
        t2 = "02 Current(affairs)"
        t3 = "03 Information()"
        t4 = "04 Sport()"
        t5 = "05 Education()"
        t6 = "06 Drama()"
        t7 = "07 Culture()"
        t8 = "08 Science()"
        t9 = "09 Varied()"
        t10 = "10 Pop(music)"
        t11 = "11 Rock(music)"
        t12 = "12 Easy(listening)"
        t13 = "13 Light(classical)"
        t14 = "14 Serious(classical)"
        t15 = "15 Other(music)"
        t16 = "16 Weather()"
        t17 = "17 Finance()"
        t18 = "18 Children()"
        t19 = "19 Social(affairs)"
        t20 = "20 Religion()"
        t21 = "21 Phone-in"
        t22 = "22 Travel()"
        t23 = "23 Leisure()"
        t24 = "24 Jazz(music)"
        t25 = "25 Country(music)"
        t26 = "26 National(music)"
        t27 = "27 Oldies(music)"
        t28 = "28 Folk(music)"
        t29 = "29 Documentary()"
        t30 = "30 Alarm(Test)"
        t31 = "31 Alarm()"
        t32 = "Error"
        if pty > 32:
            pty = 32

        ptyTuple = (t0, t1, t2, t3, t4, t5, t6, t7, t8, t9, t10, t11, t12, t13, t14, t15, t16,t17, t18, t19, t20, t21,
                    t22, t23, t24, t25, t26, t27, t28, t29, t30, t31, t32)

        # print('Program type : ' + str(ptyTuple[pty]))
        self.lineEditProgramType.setText(str(ptyTuple[pty]))

        # Type Group
        groupType = RDSB_H & 0xF0
        # Group 0
        if groupType == 0x0:
            diSegment = RDSB_L & 0x03
            di = RDSB_L & 0x07
            ta = RDSB_L & 0x10
            tp = RDSB_H & 0x04
            ms = RDSB_L & 0x08
            dataStr = hex(di)
            dataStr = dataStr.replace("0x", "")
            self.lineEditDI.setText(dataStr)
            if ta == 0x10:
                self.labelTA.setStyleSheet("background-color: lightgreen;")
            else:
                self.labelTA.setStyleSheet("background-color: lightgray;")
            if tp == 0x04:
                self.labelTP.setStyleSheet("background-color: lightgreen;")
            else:
                self.labelTP.setStyleSheet("background-color: lightgray;")
            if ms == 0x08:
                self.labelMS.setStyleSheet("background-color: lightgreen;")
            else:
                self.labelMS.setStyleSheet("background-color: lightgray;")

            # print('diSegment : ' + str(diSegment))
            # print('di : ' + str(di))
            # print('ta : ' + str(ta))
            # print('ms : ' + str(ms))

            l0 = "Mono"
            l1 = "Stereo"
            l2 = "Not Artificial Head"
            l3 = "Artificial Head"
            l4 = "Not Compressed"
            l5 = "Compressed"
            l6 = "Static PTY"
            l7 = "Dynamic PTY"

            if di == 0:
                self.lineEditStereo.setText(l0)
            elif di == 4:
                self.lineEditStereo.setText(l1)
            elif di == 1:
                self.lineEditHead.setText(l2)
            elif di == 5:
                self.lineEditHead.setText(l3)
            elif di == 2:
                self.lineEditCompressed.setText(l4)
            elif di == 6:
                self.lineEditCompressed.setText(l5)
            elif di == 3:
                self.lineEditPTY.setText(l6)
            elif di == 7:
                self.lineEditPTY.setText(l7)

            if (RDSD_H < 0x20 | RDSD_H > 0x7E):
                RDSD_H  = 0x20
            if (RDSD_L < 0x20 | RDSD_L > 0x7E):
                RDSD_L  = 0x20

            textPS = ""

            if diSegment == 0x0:
                PS1 = chr(RDSD_H) + chr(RDSD_L)
                self.PS[diSegment] = PS1
            elif diSegment == 0x1:
                PS2 = chr(RDSD_H) + chr(RDSD_L)
                self.PS[diSegment] = PS2
            elif diSegment == 0x2:
                PS3 = chr(RDSD_H) + chr(RDSD_L)
                self.PS[diSegment] = PS3
            elif diSegment == 0x3:
                PS4 = chr(RDSD_H) + chr(RDSD_L)
                self.PS[diSegment] = PS4
            # print('PS1 to PS4 : ' + PS1 + PS2 + PS3 + PS4)
            for iter in range(4):
                textPS = textPS + self.PS[iter]
            # print('textPS : ' + textPS)
            self.lineEditPS.setText(textPS)

        if groupType == 0x20:
            testSegment = RDSB_L & 0x0F
            textAbFlag = RDSB_L & 0x10
            textStr = chr(RDSC_H) + chr(RDSC_L) + chr(RDSD_H) + chr(RDSD_L)
            textA = ""
            textB = ""
            if textAbFlag == 0x0:
                self.RTA[testSegment] = textStr
                for iter in range(16):
                    textA = textA + self.RTA[iter]
                # print('Text A : ' + textA)
                self.lineEditTextA.setText(textA)
            if textAbFlag == 0x10:
                self.RTB[testSegment] = textStr
                for iter in range(16):
                    textB = textB + self.RTB[iter]
                # print('Text B : ' + textB)
                self.lineEditTextB.setText(textB)

        if groupType == 0x40:

            # Time
            hour = (int((RDSD_H & 0xF0) / 16)) + ((RDSC_L & 0x1) * 16)
            minute = (int((RDSD_L & 0xC0) / 64)) + ((RDSD_H & 0xF) * 4)
            localTime = RDSD_L & 0x20
            localTimeOffset = (RDSD_L & 0x1F) * 30
            minuteTemp = (hour * 60) + minute
            if localTime == 0x0:
                hour = int((minuteTemp + localTimeOffset) / 60)
                minute = (minuteTemp + localTimeOffset) - (hour * 60)
                if hour >= 24:
                    hour = hour - 24
            else:
                hour = int((minuteTemp - localTimeOffset) / 60)
                minute = (minuteTemp - localTimeOffset) - (hour * 60)
                if hour < 0:
                    hour = hour + 24
            if hour < 10:
                hourStr = "0" + str(hour)
            else:
                hourStr = str(hour)
            if minute < 10:
                minuteStr = "0" + str(minute)
            else:
                minuteStr = str(minute)
            timeStr = hourStr + " : " + minuteStr
            #            print(timeStr)
            self.lineEditTime.setText(timeStr)

            # Date
            mjd = int(((RDSC_H * 256) + (RDSC_L & 0xFE)) / 2) + ((RDSB_L & 0x03) * 32768)
            #            print("MJD : " + str(mjd))
            self.lineEditMJD.setText(str(mjd))
            # mjd = 58712 # for test
            yPrime = int((mjd - 15078.2) / 365.25)
            mPrime = int((mjd - 14956.1 - int(yPrime * 365.25)) / 30.6001)
            d = mjd - 14956 - int(yPrime * 365.25) - int(mPrime * 30.6001)
            if mPrime == 14 or mPrime == 15:
                k = 1
            else:
                k = 0
            y = yPrime + k + 1900
            m = mPrime - 1 - (k * 12)
            dw = (mjd + 2) - (int((mjd + 2) / 7) * 7)
            week = ("Monday ", "Tuesday ", "Wednesday ", "Thursday ", "Friday ", "Saturday", "Sunday ")
            day = week[dw]

            dateStr = day + str(d) + " / " + str(m) + " / " + str(y)
            #            print(dateStr)
            self.lineEditDate.setText(dateStr)

    def seekUpButtonPressed(self):
        """Searches for a new radio station on a higher frequency
            This is executed when the seekUp button is pressed
        """
        self.bufferOut[0] = 0x00
        self.bufferOut[1] = 0x31
        self.bufferOut[2] = 0x00
        self.bufferOut[3] = 0x03
        self.bufferOut[4] = 0x00
        self.bufferOut[5] = 0x00
        self.bufferOut[6] = 0x00
        dataOut = self.buffertostring(self.bufferOut)
        self.lineEditBufferOut.setText(dataOut)
        dataOut = bytes(bytearray(self.bufferOut))
        self.hidSend(dataOut)
        # self.clearTextBox2()

    def seekDownButtonPressed(self):
        """Searches for a new radio station on a lower frequency
            This is executed when the seekDown button is pressed
        """
        self.bufferOut[0] = 0x00
        self.bufferOut[1] = 0x31
        self.bufferOut[2] = 0x00
        self.bufferOut[3] = 0x01
        self.bufferOut[4] = 0x00
        self.bufferOut[5] = 0x00
        self.bufferOut[6] = 0x00
        dataOut = self.buffertostring(self.bufferOut)
        self.lineEditBufferOut.setText(dataOut)
        dataOut = bytes(bytearray(self.bufferOut))
        self.hidSend(dataOut)
        # self.clearTextBox2()

    def tuneUpButtonPressed(self):
        """Searches for a new radio station on a higher frequency
            This is executed when the seekUp button is pressed
        """
        channel = ((0 + 875) + 1) * 10
        if channel == 8740:
            channel = 10800
        self.bufferOut[0] = 0x00
        self.bufferOut[1] = 0x31
        self.bufferOut[2] = 0x00
        self.bufferOut[3] = channel & 0xFF
        self.bufferOut[4] = int((channel & 0xFF00) / 256)
        self.bufferOut[5] = 0x00
        self.bufferOut[6] = 0x00
        dataOut = self.buffertostring(self.bufferOut)
        self.lineEditBufferOut.setText(dataOut)
        dataOut = bytes(bytearray(self.bufferOut))
        self.hidSend(dataOut)
        # self.clearTextBox2()

    def tuneDownButtonPressed(self):
        """Searches for a new radio station on a lower frequency
            This is executed when the seekDown button is pressed
        """
        channel = ((0 + 875) - 1) * 10
        if channel == 8740:
            channel = 10800
        self.bufferOut[0] = 0x00
        self.bufferOut[1] = 0x30
        self.bufferOut[2] = 0x00
        self.bufferOut[3] = channel & 0xFF
        self.bufferOut[4] = int((channel & 0xFF00) / 256)
        self.bufferOut[5] = 0x00
        self.bufferOut[6] = 0x00
        dataOut = self.buffertostring(self.bufferOut)
        self.lineEditBufferOut.setText(dataOut)
        dataOut = bytes(bytearray(self.bufferOut))
        self.hidSend(dataOut)
        # self.clearTextBox2()

    def checkBoxMonoClicked(self):
        """Changes Mono or Stereo
            Mono is executed when Mono checkBox is checked
            stereo is executed when Mono checkBox is no checked
        """
        self.bufferOut[0] = 0x00
        self.bufferOut[1] = 0x13
        self.bufferOut[2] = 0x00
        self.bufferOut[3] = 0x02
        self.bufferOut[4] = 0x03
        if self.checkBoxMono.isChecked():
            self.bufferOut[5] = 0x01
        else:
            self.bufferOut[5] = 0x00
        self.bufferOut[6] = 0x00
        dataOut = self.buffertostring(self.bufferOut)
        self.lineEditBufferOut.setText(dataOut)
        dataOut = bytes(bytearray(self.bufferOut))
        self.hidSend(dataOut)

    def checkBoxMuteClicked(self):
        """Changes Mute or no Mute
            Mute is executed when Mute checkBox is checked
            No mute is executed when Mute checkBox is no checked
        """
        self.bufferOut[0] = 0x00
        self.bufferOut[1] = 0x13
        self.bufferOut[2] = 0x00
        self.bufferOut[3] = 0x01
        self.bufferOut[4] = 0x03
        if self.checkBoxMute.isChecked():
            self.bufferOut[5] = 0x03
        else:
            self.bufferOut[5] = 0x00
        self.bufferOut[6] = 0x00
        dataOut = self.buffertostring(self.bufferOut)
        self.lineEditBufferOut.setText(dataOut)
        dataOut = bytes(bytearray(self.bufferOut))
        self.hidSend(dataOut)

    def comboBoxDeEmphasisSelected(self):
        """

        :return:
        """
        self.bufferOut[0] = 0x00
        self.bufferOut[1] = 0x13
        self.bufferOut[2] = 0x00
        self.bufferOut[3] = 0x00
        self.bufferOut[4] = 0x39
        match self.comboBoxDeEmphasis.currentIndex():
            case 0:
                self.bufferOut[5] = 0x00
            case 1:
                self.bufferOut[5] = 0x01
            case 2:
                self.bufferOut[5] = 0x02
        self.bufferOut[6] = 0x00
        # hex(x) for x in a_list
        dataOut = self.buffertostring(self.bufferOut)
        self.lineEditBufferOut.setText(dataOut)
        dataOut = bytes(bytearray(self.bufferOut))
        self.hidSend(dataOut)

    def horizontalScrollBarVolumeChanged(self):
        """

        :return:
        """
        self.labelVolume = self.horizontalScrollBarVolume.value()
        self.bufferOut[0] = 0x00
        self.bufferOut[1] = 0x13
        self.bufferOut[2] = 0x00
        self.bufferOut[3] = 0x00
        self.bufferOut[4] = 0x03
        self.bufferOut[5] = self.horizontalScrollBarVolume.value()
        self.bufferOut[6] = 0x00
        dataOut = self.buffertostring(self.bufferOut)
        self.lineEditBufferOut.setText(dataOut)
        dataOut = bytes(bytearray(self.bufferOut))
        self.hidSend(dataOut)


    def changeValue(self, value):
        if value != "":
            value = math.floor(int(value) / 10)
        else:
            value = "8960"
        self.com.updateDisplay.emit(value)
        self.radioDisplay.repaint()

    def hidSend(self, dataOut=b"\x00"):
        """Sends a command for the USB HID device
        Args:
            dataOut: byte, command to the device
        """
        try:
            res1 = self.myDevice.write(dataOut)
            dataOutStr = ""
            for data in dataOut:
                dataOutStr += str("{0:02X}".format(data)) + " "
        except Exception:
            msgBox = QMessageBox()
            msgBox.setWindowTitle("Message")
            msgBox.setText("Writing error")
            msgBox.setStandardButtons(QMessageBox.StandardButton.Cancel)
            msgBox.setDefaultButton(QMessageBox.StandardButton.Cancel)
            answer = msgBox.exec()
            if answer == QMessageBox.StandardButton.Cancel:
                pass

# PRESET RADIOS

    def enablePresetsSelected(self):
        """Enables all presets if Memory checkBox is checked
            self displays all presets
        """
        if self.checkBoxMemory.isChecked():
            self.pushButtonPreset1.setEnabled(True)
            self.pushButtonPreset2.setEnabled(True)
            self.pushButtonPreset3.setEnabled(True)
            self.pushButtonPreset4.setEnabled(True)
            self.pushButtonPreset5.setEnabled(True)
            self.pushButtonPreset6.setEnabled(True)
            self.pushButtonPreset7.setEnabled(True)
            self.pushButtonPreset8.setEnabled(True)
            self.pushButtonPreset9.setEnabled(True)
            self.pushButtonPreset10.setEnabled(True)
            self.pushButtonPreset11.setEnabled(True)
            self.pushButtonPreset12.setEnabled(True)
            self.pushButtonPreset13.setEnabled(True)
            self.pushButtonPreset14.setEnabled(True)
            self.pushButtonPreset15.setEnabled(True)
            self.pushButtonPreset16.setEnabled(True)
        else:
            self.loadSettingsIni()

    def buttonPresetPressed(self, index):
        """Save the indexed preset after validation
            if Memory checkedBox is checked
            else load the indexed preset.

        Args:
            index: int, ident of the chosen preset
        """
        if self.checkBoxMemory.isChecked():
            msgBox = QMessageBox()
            msgBox.setWindowTitle("Message")
            msgBox.setText("Add or Modify preset")
            msgBox.setInformativeText("Are you sure?")
            msgBox.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            msgBox.setDefaultButton(QMessageBox.StandardButton.No)
            answer = msgBox.exec()
            if answer == QMessageBox.StandardButton.Yes:
                newName = self.lineEditPS.text()
                if self.lineEditFrequencyValue.text() != "":
                    newChannel = int(self.lineEditFrequencyValue.text()) / 100
                else:
                    newChannel = "88.0"
                radios[index].name = newName
                radios[index].enable = True
                radios[index].channel = newChannel
                self.saveSettings()

            if answer == QMessageBox.StandardButton.No:
                pass

        else:
            self.clearTextBox()
            frequencyRadio = radios[index].channel
            self.bufferOut[0] = 0x00
            self.bufferOut[1] = 0x30
            self.bufferOut[2] = 0x00
            self.bufferOut[3] = int(frequencyRadio * 100) & 0xFF
            print(self.bufferOut[3])
            self.bufferOut[4] = int(((int(frequencyRadio * 100)) & 0xFF00) / 256)
            print(self.bufferOut[4])
            self.bufferOut[5] = 0x00
            self.bufferOut[6] = 0x00
            self.bufferOut[7] = 0x00
            dataOut = self.buffertostring(self.bufferOut)
            self.lineEditBufferOut.setText(dataOut)
            dataOut = bytes(bytearray(self.bufferOut))
            print(dataOut)
            self.hidSend(dataOut)


    def disableAllPresets(self):
        """Disables all presets"""
        self.pushButtonPreset1.setEnabled(False)
        self.pushButtonPreset2.setEnabled(False)
        self.pushButtonPreset3.setEnabled(False)
        self.pushButtonPreset4.setEnabled(False)
        self.pushButtonPreset5.setEnabled(False)
        self.pushButtonPreset6.setEnabled(False)
        self.pushButtonPreset7.setEnabled(False)
        self.pushButtonPreset8.setEnabled(False)
        self.pushButtonPreset9.setEnabled(False)
        self.pushButtonPreset10.setEnabled(False)
        self.pushButtonPreset11.setEnabled(False)
        self.pushButtonPreset12.setEnabled(False)
        self.pushButtonPreset13.setEnabled(False)
        self.pushButtonPreset14.setEnabled(False)
        self.pushButtonPreset15.setEnabled(False)
        self.pushButtonPreset16.setEnabled(False)

    def loadSettingsIni(self):
        """Displays all presets on the panel"""
        self.pushButtonPreset1.setText(radios[0].name.strip())
        self.pushButtonPreset1.setEnabled(radios[0].enable)
        self.pushButtonPreset2.setText(radios[1].name.strip())
        self.pushButtonPreset2.setEnabled(radios[1].enable)
        self.pushButtonPreset3.setText(radios[2].name.strip())
        self.pushButtonPreset3.setEnabled(radios[2].enable)
        self.pushButtonPreset4.setText(radios[3].name.strip())
        self.pushButtonPreset4.setEnabled(radios[3].enable)
        self.pushButtonPreset5.setText(radios[4].name.strip())
        self.pushButtonPreset5.setEnabled(radios[4].enable)
        self.pushButtonPreset6.setText(radios[5].name.strip())
        self.pushButtonPreset6.setEnabled(radios[5].enable)
        self.pushButtonPreset7.setText(radios[6].name.strip())
        self.pushButtonPreset7.setEnabled(radios[6].enable)
        self.pushButtonPreset8.setText(radios[7].name.strip())
        self.pushButtonPreset8.setEnabled(radios[7].enable)
        self.pushButtonPreset9.setText(radios[8].name.strip())
        self.pushButtonPreset9.setEnabled(radios[8].enable)
        self.pushButtonPreset10.setText(radios[9].name.strip())
        self.pushButtonPreset10.setEnabled(radios[9].enable)
        self.pushButtonPreset11.setText(radios[10].name.strip())
        self.pushButtonPreset11.setEnabled(radios[10].enable)
        self.pushButtonPreset12.setText(radios[11].name.strip())
        self.pushButtonPreset12.setEnabled(radios[11].enable)
        self.pushButtonPreset13.setText(radios[12].name.strip())
        self.pushButtonPreset13.setEnabled(radios[12].enable)
        self.pushButtonPreset14.setText(radios[13].name.strip())
        self.pushButtonPreset14.setEnabled(radios[13].enable)
        self.pushButtonPreset15.setText(radios[14].name.strip())
        self.pushButtonPreset15.setEnabled(radios[14].enable)
        self.pushButtonPreset16.setText(radios[15].name.strip())
        self.pushButtonPreset16.setEnabled(radios[15].enable)

    def saveSettings(self):
        """Save all presets on json file"""
        settings = {}
        for radio in radios:
            id = radio.id
            name = radio.name
            enable = radio.enable
            channel = radio.channel
            favIndex = "preset" + str(id)
            favDict = {
             "channel": channel,
             "enable": enable,
             "id": id,
             "name": name
            }
            settings[favIndex] = favDict
        # Serializing json
        json_object = json.dumps(settings, indent=4)
        with open("radioSettings.json", "w") as outfile:
            outfile.write(json_object)
def main():
    """Main program"""
    app = QApplication(sys.argv)
    window = Fm()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
