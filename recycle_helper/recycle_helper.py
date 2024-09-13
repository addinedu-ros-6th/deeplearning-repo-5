import sys
import cv2
import socket
import struct
import pickle
import threading
import random
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel
from PyQt5.QtCore import QThread, pyqtSignal, QTimer, Qt, QEvent, QSize
from PyQt5.QtGui import QPixmap, QIcon, QMovie, QFont, QFontDatabase, QImage
import torch

class ServerThread(QThread):
    update_frame = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.cap = cv2.VideoCapture(0)
        self.server_ip = '0.0.0.0'
        self.server_port = 22223
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.server_ip, self.server_port))
        self.server_socket.listen(5)
        self.running = True

    def run(self):
        print(f"서버가 {self.server_ip}:{self.server_port}에서 대기 중...")
        while self.running:
            client_socket, client_address = self.server_socket.accept()
            print(f"클라이언트 연결됨: {client_address}")
            threading.Thread(target=self.client_thread, args=(client_socket,)).start()

    def client_thread(self, client_socket):
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                print("웹캠에서 프레임을 읽을 수 없습니다.")
                break

            data = pickle.dumps(frame)
            data_size = len(data)
            client_socket.sendall(struct.pack('L', data_size))
            client_socket.sendall(data)

            try:
                data_size_bytes = client_socket.recv(struct.calcsize('L'))
                if not data_size_bytes:
                    print("클라이언트와의 연결이 끊어졌습니다.")
                    break

                data_size = struct.unpack('L', data_size_bytes)[0]
                data = b''
                while len(data) < data_size:
                    packet = client_socket.recv(data_size - len(data))
                    if not packet:
                        print("클라이언트와의 연결이 끊어졌습니다.")
                        break
                    data += packet

                result_frame = pickle.loads(data)
                self.update_frame.emit(result_frame)

            except Exception as e:
                print(f"오류 발생: {e}")
                break

        client_socket.close()

    def stop(self):
        self.running = False
        self.cap.release()
        self.server_socket.close()

class WebcamServerApp(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi('recycle_helper.ui', self)

        self.gif_Labels = []  # 전역 변수로 사용하기 위해 클래스 변수로 초기화
        self.load_custom_font()
        
        # Initialize buttons and labels
        self.initialize_ui()

        # Initialize server thread
        self.server_thread = ServerThread()
        self.server_thread.update_frame.connect(self.update_frame)
        self.server_thread.start()

    def initialize_ui(self):
        self.gif_Labels = [
            self.plastic_gif_Label, self.can_gif_Label, self.paper_gif_Label,
            self.styrofoam_gif_Label, self.glass_gif_Label, self.vinyl_gif_Label
        ]
        
        self.plastic_Label.setText('플라스틱')
        self.can_Label.setText('캔')
        self.paper_Label.setText('종이')
        self.styrofoam_Label.setText('스티로폼')
        self.glass_Label.setText('유리')
        self.vinyl_Label.setText('비닐')

        self.button_images = {
            'plastic_Button': {
                'initial': '/home/jun/dev_ws/dl_project/img_src/pixelated_trash_can_by.jpeg',
                'hover': '/home/jun/dev_ws/dl_project/img_src/trash_can_3.jpg',
                'clicked': '/home/jun/dev_ws/dl_project/img_src/pixelated_opened_trash_can_by.jpeg'
            },
            'can_Button': {
                'initial': '/home/jun/dev_ws/dl_project/img_src/pixelated_trash_can_bw.jpeg',
                'hover': '/home/jun/dev_ws/dl_project/img_src/trash_can_3.jpg',
                'clicked': '/home/jun/dev_ws/dl_project/img_src/pixelated_opened_trash_can_by.jpeg'
            },
            'paper_Button': {
                'initial': '/home/jun/dev_ws/dl_project/img_src/pixelated_trash_can_br.jpeg',
                'hover': '/home/jun/dev_ws/dl_project/img_src/trash_can_3.jpg',
                'clicked': '/home/jun/dev_ws/dl_project/img_src/pixelated_opened_trash_can_by.jpeg'
            },
            'styrofoam_Button': {
                'initial': '/home/jun/dev_ws/dl_project/img_src/pixelated_trash_can_bm.jpeg',
                'hover': '/home/jun/dev_ws/dl_project/img_src/trash_can_3.jpg',
                'clicked': '/home/jun/dev_ws/dl_project/img_src/pixelated_opened_trash_can_by.jpeg'
            },
            'glass_Button': {
                'initial': '/home/jun/dev_ws/dl_project/img_src/pixelated_trash_can_bg.jpeg',
                'hover': '/home/jun/dev_ws/dl_project/img_src/trash_can_3.jpg',
                'clicked': '/home/jun/dev_ws/dl_project/img_src/pixelated_opened_trash_can_by.jpeg'
            },
            'vinyl_Button': {
                'initial': '/home/jun/dev_ws/dl_project/img_src/pixelated_trash_can_bb.jpeg',
                'hover': '/home/jun/dev_ws/dl_project/img_src/trash_can_3.jpg',
                'clicked': '/home/jun/dev_ws/dl_project/img_src/pixelated_opened_trash_can_by.jpeg'
            }
        }

        self.original_size = (100, 100)  # Original button size
        self.hover_size = QSize(150, 150)  # Size when hovering
        self.hover_gif_path = "/home/jun/dev_ws/dl_project/img_src/agree.gif"  # GIF path

        self.set_initial_images()

        for button_name in self.button_images.keys():
            button = getattr(self, button_name)
            gif_label = QLabel(self)
            gif_label.setFixedSize(self.hover_size)
            gif_label.setStyleSheet("background: transparent;")
            gif_label.hide()
            self.gif_Labels.append(gif_label)

        for button_name in self.button_images.keys():
            button = getattr(self, button_name)
            button.installEventFilter(self)

        self.main_Label = self.findChild(QLabel, 'main_Label')
        self.stop_button = self.findChild(QPushButton, 'stop_button')

        self.tips = [
            "알고 있으십니까?\n빨대는 일반쓰레기입니다.",
            "알고 있으십니까?\n뼈, 조개 껍데기 등등 단단한건 일반쓰레기입니다.",
            "알고 있으십니까?\n칼이나 가위 같은 날카로운 물체는 운반 과정 중에 위험하므로 날카로운 부분을 종이로 싸매서 종량제 봉투로 배출합니다.",
            "알고 있으십니까?\n기름은 절대 배수구에 버리지 않도록합니다. 굳히거나 흡수시켜 일반쓰레기로 배출합니다",
            "알고 있으십니까?\n페트병은 라벨을 제거해서 라벨은 비닐, 페트병은 투명과 유색을 구분해서 배출합니다.",
            "알고 있으십니까?\n이글을 보고 있는 당신 꽤나 멋집니다.",
            "알고 있으십니까?\n어떻게 버려야할지 모른다면 재활용 마크를 보면 됩니다. 없다면 일반쓰레기입니다",
            "알고 있으십니까?\n당장은 어려워도 습관이 되면 무의식이 처리합니다.",
            "알고 있으십니까?\n우산은 분리해서 금속과 일반쓰레기로 나누어 배출합니다."
        ]
        self.sub_Label.setVisible(True)
        self.comment_Label.setVisible(True)
        random_tip = random.choice(self.tips)
        self.comment_Label.setText(random_tip)
        self.comment_Label.setWordWrap(True)
        self.comment_Label.setVisible(True)
        self.comment_Label.setStyleSheet("font-size: 15pt; font-family: 'DungGeunMo';")

        self.loading_movie = QMovie("/home/jun/dev_ws/dl_project/img_src/cat.gif")
        self.main_Label.setMovie(self.loading_movie)
        self.loading_movie.start()

        self.stop_button.clicked.connect(self.stop_server)

    def set_initial_images(self):
        for button_name, images in self.button_images.items():
            button = getattr(self, button_name)
            self.set_button_image(button, images['initial'])

    def set_button_image(self, button, image_path):
        pixmap = QPixmap(image_path)
        pixmap = pixmap.scaled(button.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        button.setIcon(QIcon(pixmap))
        button.setIconSize(pixmap.size())

    def stop_server(self):
        if self.server_thread:
            self.server_thread.stop()
            self.server_thread.wait()  # Wait for the thread to stop completely

        self.initialize_ui()  # Re-initialize everything

    def restart_gif(self):
        self.loading_movie = QMovie("/home/jun/dev_ws/dl_project/img_src/cat.gif")
        self.main_Label.setMovie(self.loading_movie)
        self.loading_movie.start()
        self.main_Label.repaint()

    def update_frame(self, frame):
        frame_ = frame[0].plot()
        cls_ = frame[0].boxes.cls.item()
        h, w, ch = frame_.shape
        result = cv2.cvtColor(frame_, cv2.COLOR_BGR2RGB)
        q_img = QImage(result.data, w, h, ch * w, QImage.Format_RGB888)
        self.main_Label.setPixmap(QPixmap.fromImage(q_img))
        self.sub_Label.setVisible(False)
        self.comment_Label.setVisible(False)
        self.classification(cls_)

    def classification(self, index):
        buttons = [
            self.plastic_Button, 
            self.can_Button, 
            self.paper_Button, 
            self.styrofoam_Button, 
            self.glass_Button, 
            self.vinyl_Button
        ]

        # Disable all buttons first
        for button in buttons:
            button.setDisabled(True)
        
        # Enable only the button corresponding to the index
        if 0 <= int(index) < len(buttons):
            buttons[int(index)].setDisabled(False)

    def load_custom_font(self):
        font_id = QFontDatabase.addApplicationFont('font/DungGeunMo.ttf')
        font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
        self.font = QFont(font_family)
        self.set_font_to_widgets()

    def set_font_to_widgets(self):
        self.comment_Label.setFont(self.font)
        self.plastic_Label.setFont(self.font)
        self.can_Label.setFont(self.font)
        self.paper_Label.setFont(self.font)
        self.styrofoam_Label.setFont(self.font)
        self.glass_Label.setFont(self.font)
        self.vinyl_Label.setFont(self.font)

    def show_gif(self, button_name, button):
        gif_label = self.get_gif_label_from_button(button_name)
        if gif_label:
            gif_movie = QMovie(self.hover_gif_path)
            gif_movie.setScaledSize(gif_label.size())
            gif_label.setMovie(gif_movie)
            gif_movie.start()
            gif_label.show()

    def hide_gif(self, button_name):
        gif_label = self.get_gif_label_from_button(button_name)
        if gif_label:
            gif_label.movie().stop()
            gif_label.hide()

    def get_gif_label_from_button(self, button_name):
        for gif_label in self.gif_Labels:
            if button_name.split('_')[0] in str(gif_label.objectName()):
                return gif_label
        return None

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Enter:
            # Check if the object is a button and if it is enabled
            if obj.isEnabled():
                button_name = self.get_button_name_from_widget(obj)
                if button_name:
                    self.show_gif(button_name, obj)
        elif event.type() == QEvent.Leave:
            # Check if the object is a button and if it is enabled
            if obj.isEnabled():
                button_name = self.get_button_name_from_widget(obj)
                if button_name:
                    self.hide_gif(button_name)

        return super().eventFilter(obj, event)

    def get_button_name_from_widget(self, widget):
        for button_name, button in self.__dict__.items():
            if button == widget:
                return button_name
        return None

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WebcamServerApp()
    window.show()
    sys.exit(app.exec_())
