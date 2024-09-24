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
import mysql.connector
from datetime import datetime

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

        # Initialize server thread
        self.server_thread = ServerThread()
        self.server_thread.update_frame.connect(self.update_frame)
        self.server_thread.start()

        self.dump_Button.setDisabled(True)
        self.dump_Button.clicked.connect(self.on_dump_button_clicked)

        self.main_Label = self.findChild(QLabel, 'main_Label')
        self.refresh_button = self.findChild(QPushButton, 'refresh_button')

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

        self.loading_movie = QMovie("img_src/cat.gif")
        self.main_Label.setMovie(self.loading_movie)
        self.loading_movie.start()

        self.refresh_Button.clicked.connect(self.refresh_comment)

    def refresh_comment(self):
        random_tip = random.choice(self.tips)
        self.comment_Label.setText(random_tip)
        self.comment_Label.setWordWrap(True)

    def update_frame(self, frame):
        frame_ = frame[0].plot()
        cls_ = int(frame[0].boxes.cls.item())
        h, w, ch = frame_.shape
        result = cv2.cvtColor(frame_, cv2.COLOR_BGR2RGB)
        q_img = QImage(result.data, w, h, ch * w, QImage.Format_RGB888)
        self.main_Label.setPixmap(QPixmap.fromImage(q_img))
        self.sub_Label.setVisible(False)
        self.comment_Label.setVisible(False)

        self.current_classification = int(cls_)
        if self.current_classification != 0 and self.current_classification != 4:
            self.dump_Button.setEnabled(True)
        else:
            self.dump_Button.setDisabled(True)

    def on_dump_button_clicked(self):
            self.insert_data(self.current_classification)  # 저장된 분류를 데이터베이스에 삽입

    def insert_data(self, classification):
        if classification == 1:
            classification = '유리'
        elif classification == 2:
            classification = '캔'
        elif classification == 3:
            classification = '플라스틱'
        try:
            connection = mysql.connector.connect(
                host="database-1.cpwy8c66woni.ap-northeast-2.rds.amazonaws.com",
                port=3306,
                user="admin",
                password="lolmh0211",
                database="DL_project"
            )

            cursor = connection.cursor()
            current_time = datetime.now()
            query = "INSERT INTO trash (time, class) VALUES (%s, %s)"
            cursor.execute(query, (current_time, classification))

            connection.commit()
            print(f"{classification}가 데이터베이스에 추가되었습니다.")

        except mysql.connector.Error as err:
            print(f"데이터베이스 오류: {err}")

        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

    def load_custom_font(self):
        font_id = QFontDatabase.addApplicationFont('font/DungGeunMo.ttf')
        font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
        self.font = QFont(font_family)
        self.set_font_to_widgets()

    def set_font_to_widgets(self):
        self.comment_Label.setFont(self.font)
        self.dump_Button.setFont(self.font)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WebcamServerApp()
    window.show()
    sys.exit(app.exec_())
