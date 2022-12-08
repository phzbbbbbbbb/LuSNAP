import os
import re
import cv2
import sys
import json
from tqdm import tqdm
import PyQt5
from threading import Thread
from functions.slicing import Data
import numpy as np
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import matplotlib
matplotlib.use("Qt5Agg")  # 声明使用pyqt5
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg  # pyqt5的画布
import matplotlib.pyplot as plt
# matplotlib.figure 模块提供了顶层的Artist(图中的所有可见元素都是Artist的子类)，它包含了所有的plot元素
from matplotlib.figure import Figure

FIGSIZE = 1024


class MyMatplotlibFigure(FigureCanvasQTAgg):
    """
    创建一个画布类，并把画布放到FigureCanvasQTAgg
    """
    def __init__(self, width=10, heigh=10, dpi=100):
        # plt.rcParams['figure.facecolor'] = 'r'  # 设置窗体颜色
        # plt.rcParams['axes.facecolor'] = 'b'  # 设置绘图区颜色
        # 创建一个Figure,该Figure为matplotlib下的Figure，不是matplotlib.pyplot下面的Figure
        # 这里还要注意，width, heigh可以直接调用参数，不能用self.width、self.heigh作为变量获取，因为self.width、self.heigh 在模块中已经FigureCanvasQTAgg模块中使用，这里定义会造成覆盖
        self.figs = Figure(figsize=(width, heigh), dpi=dpi)
        super(MyMatplotlibFigure, self).__init__(self.figs)  # 在父类种激活self.fig， 否则不能显示图像（就是在画板上放置画布）
        self.axes = self.figs.add_subplot(111)  # 添加绘图区
        self.axes.spines['top'].set_visible(False)  # 顶边界不可见
        self.axes.spines['right'].set_visible(False)  # 右边界不可见


class MainLayout(QMainWindow):

    def __init__(self):
        super(MainLayout, self).__init__()
        self.initUI()

        self.loc_x = 0
        self.loc_y = 0
        self.loc_z = 0

        with open(r"style.qss", 'r') as q:
            self.setStyleSheet(q.read())

        self.imgHeight = FIGSIZE
        self.imgWidth = FIGSIZE

        self.mhd = None
        self.mha = None

        self.maxSlice = 500


    def initUI(self):

        # 整体窗口大小
        self.setFixedSize(FIGSIZE * 2 + 500, FIGSIZE + 200)
        self.setWindowTitle("肺结节检测程序")
        self.setObjectName('win')

        # 菜单栏
        fileMenuBar = self.menuBar()
        fileMenu = fileMenuBar.addMenu('文件')
        readMhdFileAct = QAction("读取mhd文件", self)
        readMhaFileAct = QAction("读取mha文件", self)
        fileMenu.addAction(readMhdFileAct)
        fileMenu.addAction(readMhaFileAct)

        readMhaFileAct.triggered.connect(self.readMhaFile)
        readMhdFileAct.triggered.connect(self.readMhdFile)

        x_offset, y_offset = 40, 120
        yz_offset = 60

        """label的位置"""
        self.mhdLabel = QLabel(self)
        # self.mhdLabel.setText("显示mhd图像")
        # self.mhdLabel.setAlignment(Qt.AlignCenter)
        self.mhdLabel.setFixedSize(FIGSIZE, FIGSIZE)
        self.mhdLabel.move(x_offset, y_offset)
        self.mhdCanvas = MyMatplotlibFigure(width=1, heigh=1, dpi=100)
        self.hboxlayout = QtWidgets.QHBoxLayout(self.mhdLabel)
        self.hboxlayout.addWidget(self.mhdCanvas)

        self.mhaLabel = QLabel(self)
        # self.mhaLabel.setText("显示mha图像")
        self.mhaLabel.setFixedSize(FIGSIZE, FIGSIZE)
        self.mhaLabel.move(x_offset + FIGSIZE + 100, y_offset)
        self.mhaCanvas = MyMatplotlibFigure(width=1, heigh=1, dpi=100)
        self.hboxlayout = QtWidgets.QHBoxLayout(self.mhaLabel)
        self.hboxlayout.addWidget(self.mhaCanvas)

        self.mhdPath = QLineEdit(self)
        self.mhdPath.setText("mhd文件位置：")
        self.mhdPath.setFixedSize(FIGSIZE, 35)
        self.mhdPath.move(x_offset, y_offset + FIGSIZE + 15)

        self.mhaPath = QLineEdit(self)
        self.mhaPath.setText("mha文件位置：")
        self.mhaPath.setFixedSize(FIGSIZE, 35)
        self.mhaPath.move(x_offset + FIGSIZE + 100, y_offset + FIGSIZE + 15)

        self.jumpArea = QLineEdit(self)
        self.jumpArea.setFixedSize(135, 40)
        self.jumpArea.move(x_offset + FIGSIZE + 100 + FIGSIZE + 50, y_offset + 50)

        self.label_location = QLabel(self)
        self.label_location.setText(' 鼠标点击位置:')
        self.label_location.setFixedSize(285, 35)
        self.label_location.move(x_offset + FIGSIZE + 100 + FIGSIZE + 50, y_offset + 50 * 2)

        self.label_volume = QLabel(self)
        self.label_volume.setText(' 结节体积大小:')
        self.label_volume.setFixedSize(285, 35)
        self.label_volume.move(x_offset + FIGSIZE + 100 + FIGSIZE + 50, y_offset + 50 * 3)

        self.label_weight = QLabel(self)
        self.label_weight.setText(' 结节重量大小:')
        self.label_weight.setFixedSize(285, 35)
        self.label_weight.move(x_offset + FIGSIZE + 100 + FIGSIZE + 50, y_offset + 50 * 4)

        self.label_density = QLabel(self)
        self.label_density.setText(' 结节密度大小:')
        self.label_density.setFixedSize(285, 35)
        self.label_density.move(x_offset + FIGSIZE + 100 + FIGSIZE + 50, y_offset + 50 * 5)

        self.label_dia = QLabel(self)
        self.label_dia.setText(' 最大直径大小:')
        self.label_dia.setFixedSize(285, 35)
        self.label_dia.move(x_offset + FIGSIZE + 100 + FIGSIZE + 50, y_offset + 50 * 6)

        self.label_section_density = QLabel(self)
        self.label_section_density.setText(' 截面密度大小:')
        self.label_section_density.setFixedSize(285, 35)
        self.label_section_density.move(x_offset + FIGSIZE + 100 + FIGSIZE + 50, y_offset + 50 * 7)

        self.log_area = QPlainTextEdit(self)
        self.log_area.setFixedSize(285, 600)
        self.log_area.move(x_offset + FIGSIZE + 100 + FIGSIZE + 50, y_offset + 50 * 8 + 10)

        """button的位置"""
        self.btn_image = QPushButton(self)
        self.btn_image.setText("神秘按键")
        self.btn_image.move(x_offset, yz_offset)

        self.btn_last = QPushButton(self)
        self.btn_last.setText("<-上一张图片")
        self.btn_last.move(x_offset + FIGSIZE + 100 + FIGSIZE + 50, y_offset)
        self.btn_last.setShortcut("Left")
        self.btn_last.clicked.connect(self.btnLast)

        self.btn_next = QPushButton(self)
        self.btn_next.setText("下一张图片->")
        self.btn_next.move(x_offset + FIGSIZE + 100 + FIGSIZE + 50 + 150, y_offset)
        self.btn_next.setShortcut("Right")
        self.btn_next.clicked.connect(self.btnNext)

        self.btn_jump = QPushButton(self)
        self.btn_jump.setText("跳转")
        self.btn_jump.move(x_offset + FIGSIZE + 100 + FIGSIZE + 50 + 155, y_offset + 52)
        self.btn_jump.clicked.connect(self.btnJump)

        ''' slider的位置 '''
        self.sld = QSlider(Qt.Vertical,self)
        self.sld.setGeometry(FIGSIZE + 75, 120, 30, FIGSIZE)
        self.sld.setMinimum(0)
        self.sld.setMaximum(99)

        self.sld.valueChanged[int].connect(self.changeSlice)

    def changeSlice(self):
        self.loc_z = self.sld.value()
        self.label_location.setText(' 鼠标点击位置: ' + str(self.loc_y) + ',' + str(self.loc_x) + ',' + str(self.loc_z))
        self.plotMha()
        self.plotMhd()

    def readMhdFile(self):
        mhdPath, _ = QFileDialog.getOpenFileName(self, "Open file")
        self.mhd = Data(mhdPath)
        self.maxSlice = min(self.mhd._image.shape[0] - 1, self.maxSlice)
        self.sld.setMaximum(self.maxSlice)
        self.mhdPath.setText("mhd文件位置：%s" % self.mhd.path)
        self.plotMhd()
        self.normalOutputWritten("mhd文件读取成功\n")
        print(f'mhd 文件的大小为 {self.mhd._image.shape}')

    # TODO: 读取mha文件后可以在滑块上增加标记（可能会增加处理时间）
    def readMhaFile(self):
        mhaPath, _ = QFileDialog.getOpenFileName(self, "Open file")
        self.mha = Data(mhaPath)
        self.maxSlice = min(self.mha._image.shape[0]-1, self.maxSlice)
        self.sld.setMaximum(self.maxSlice)
        self.mhaPath.setText("mha文件位置：%s" % self.mha.path)
        self.plotMha()
        self.normalOutputWritten("mha文件读取成功\n")
        print(f'mha 文件的大小为 {self.mha._image.shape}')

    # TODO: 在matplotlib上没有正确执行，可以尝试在最外层加一层透明label?
    def mousePressEvent(self, e):
        '''
        鼠标点击位置的坐标转换
        '''
        x = e.pos().x()
        y = e.pos().y()
        if x >= 40 and x <= 740 and y >= 120 and y <= 820:
            self.loc_x = int((x-40) * self.imgWidth/700)
            self.loc_y = int((y-120) * self.imgHeight/700)
        elif x >= 840 and x <= 1540 and y >= 120 and y <= 820:
            self.loc_x = int((x-840) * self.imgWidth/700)
            self.loc_y = int((y-120) * self.imgHeight/700)
        self.label_location.setText(' 鼠标点击位置: ' + str(self.loc_y) + ',' + str(self.loc_x)+ ',' + str(self.loc_z))

    def plotMhd(self):
        if self.mhd != None:
            self.mhdCanvas.axes.cla()
            self.mhdCanvas.axes.imshow(self.mhd._image[self.loc_z])
            self.mhdCanvas.draw()
            # self.canvas.figs.suptitle("mhd")  # 设置标题

    def plotMha(self):
        if self.mha != None:
            self.mhaCanvas.axes.cla()
            self.mhaCanvas.axes.imshow(self.mha._image[self.loc_z])
            self.mhaCanvas.draw()
            # self.canvas.figs.suptitle("mha")  # 设置标题

    def btnJump(self):
        self.jumpTo(int(self.jumpArea.text()))

    def jumpTo(self, z):
        if z <= self.maxSlice and z >= 0:
            self.loc_z = z
            self.sld.setValue(z)
            self.plotMha()
            self.plotMhd()

    def btnLast(self):
        self.jumpTo(self.loc_z-1)

    def btnNext(self):
        self.jumpTo(self.loc_z+1)

    def normalOutputWritten(self, text):
        cursor = self.log_area.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertText(text)
        self.log_area.setTextCursor(cursor)
        self.log_area.ensureCursorVisible()



if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    my = MainLayout()
    my.show()
    sys.exit(app.exec_())