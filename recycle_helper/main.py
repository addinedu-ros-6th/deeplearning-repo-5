import sys
import os
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5 import uic
import random
from PyQt5.QtCore import QProcess

# Load the UI file
from_class = uic.loadUiType("main.ui")[0]

class WindowClass(QMainWindow, from_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # Set background image for label
        self.set_background_image()

        # 폰트 로드
        self.load_custom_font()

        self.tip_Label.setVisible(False)
        self.tips = [
            "알고 있으십니까?   빨대는 일반쓰레기입니다.",
            "알고 있으십니까?   뼈, 조개 껍데기 등등 단단한건 일반쓰레기입니다.",
            "알고 있으십니까?   칼이나 가위 같은 날카로운 물체는 운반 과정 중에 위험하므로 날카로운 부분을 종이로 싸매서 종량제 봉투로 배출합니다.",
            "알고 있으십니까?   기름은 절대 배수구에 버리면 안 됩니다. 굳히거나 흡수시켜 일반쓰레기로 배출합니다",
            "알고 있으십니까?   페트병은 라벨을 제거해서 라벨은 비닐, 페트병은 투명과 유색을 구분해서 배출합니다.",
            "알고 있으십니까?   이글을 보고 있는 당신 꽤나 멋집니다.",
            "알고 있으십니까?   어떻게 버려야할지 모른다면 재활용 마크를 보면 됩니다. 없다면 일반쓰레기입니다",
            "알고 있으십니까?   당장은 어려워도 습관이 되면 무의식이 처리합니다.",
            "알고 있으십니까?   우산은 분리해서 금속과 일반쓰레기로 나누어 배출합니다."
        ]
        
        self.classify_Button.clicked.connect(self.recycle_helper_window)
        self.tip_Button.clicked.connect(self.show_tip)
        self.help_Button.clicked.connect(self.show_help)

    def set_background_image(self):
        pixmap = QPixmap("img_src/background_pixel_art.jpg")
        self.label.setPixmap(pixmap.scaled(self.label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.label.setScaledContents(True)

    def load_custom_font(self):
        # 폰트 로드
        font_id = QFontDatabase.addApplicationFont('font/DNFBitBitv2.ttf')
        font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
        
        # 폰트를 기본 폰트로 설정
        self.font = QFont(font_family)
        self.set_font_to_widgets()

    def set_font_to_widgets(self):
        #모든 QLabel에 폰트 적용
        self.tip_Label.setFont(self.font)
        self.help_Button.setFont(self.font)
        self.tip_Button.setFont(self.font)
        self.classify_Button.setFont(self.font)

    def show_tip(self):
        if self.tip_Label.isVisible():
            self.tip_Label.setVisible(False)
            self.tip_Button.setText("tip")
        else:
            # 랜덤으로 문자열 선택
            random_tip = random.choice(self.tips)
            # QLabel에 선택된 문자열 표시
            self.tip_Label.setText(random_tip)
            self.tip_Label.setWordWrap(True)
            self.tip_Label.setVisible(True)
            self.tip_Button.setText("확인")

    def show_help(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle('도움말')
        msg.setText('<html><head></head><body>'
                    f'<p style="font-family:{self.font.family()}; font-size:16pt;">'
                    '분류 시작 - 카메라를 켜 쓰레기를 분리합니다.<br>'
                    '<br>'
                    'tip - 알아두면 좋은 지식을 랜덤하게 보여줍니다.'
                    '</p></body></html>')
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

    def recycle_helper_window(self):
        # Launch the webcam window as a separate process
        self.webcam_process = QProcess(self)
        self.webcam_process.start("python", ["recycle_helper.py"])
        print(1)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindows = WindowClass()
    myWindows.show()
    sys.exit(app.exec_())
