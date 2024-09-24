import sys
import mysql.connector
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QTextEdit, QVBoxLayout, QLabel, QMessageBox
from PyQt5.QtChart import QChart, QChartView, QBarSet, QBarSeries, QBarCategoryAxis, QValueAxis
from PyQt5.QtGui import QPainter

class TrashSortingApp(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('admin.ui', self)  # UI 파일 로드

        self.chart_view = QChartView(self)  # QChartView를 코드에서 생성

        # 차트 컨테이너에 레이아웃 추가
        self.chart_container = self.findChild(QLabel, 'chart_container')  # 기존 QLabel을 찾기
        layout = QVBoxLayout(self.chart_container)  # 레이아웃 설정
        layout.addWidget(self.chart_view)  # QChartView 추가

        # 로그 텍스트 박스
        self.log_text_edit = self.findChild(QTextEdit, 'log_text_edit')  # 로그 텍스트 박스 찾기

        # 버튼 클릭 이벤트 연결
        self.refresh_Button.clicked.connect(self.plot_chart)
        self.reset_Button.clicked.connect(self.reset)

        # 초기 데이터 로드
        self.update_trash_log()
        self.plot_chart()

    def fetch_data(self):
        connection = mysql.connector.connect(
                host="database-1.cpwy8c66woni.ap-northeast-2.rds.amazonaws.com",
                port=3306,
                user="admin",
                password="lolmh0211",
                database="DL_project"
            )
        cursor = connection.cursor()
        cursor.execute("SELECT datetime, type_id FROM log")
        data = cursor.fetchall()
        connection.close()
        return data

    def update_trash_log(self):
        data = self.fetch_data()
        self.log_text_edit.clear()  # 텍스트 박스 초기화
        for row in data:
            time_str = row[0].strftime("%Y-%m-%d %H:%M:%S")  # 시간 포맷 변경
            class_name = row[1]
            labels = {1: '유리', 2: '캔', 3: '플라스틱'}
            self.log_text_edit.append(f"{time_str}: {labels[class_name]}")  # 로그 형식으로 추가

    def plot_chart(self):
        data = self.fetch_data()
        set1 = QBarSet("쓰레기 종류")

        counts = {}
        for row in data:
            class_id = row[1]  # type_id를 가져옴
            counts[class_id] = counts.get(class_id, 0) + 1  # count 증가

        # 클래스 ID에 따라 이름 매핑
        labels = {1: '유리', 2: '캔', 3: '플라스틱'}

        # counts의 값을 추가
        set1.append([counts.get(1, 0), counts.get(2, 0), counts.get(3, 0)]) 

        # X축 레이블을 설정
        axisX = QBarCategoryAxis()
        axisX.append([labels[1], labels[2], labels[3]])  # 실제 레이블 추가

        series = QBarSeries()
        series.append(set1)

        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("쓰레기 분리수거 그래프")
        chart.setAnimationOptions(QChart.SeriesAnimations)

        # Y축 설정
        axisY = QValueAxis()
        axisY.setTitleText("수량")
        chart.setAxisY(axisY, series)

        # X축과 연결
        chart.setAxisX(axisX, series)

        self.chart_view.setChart(chart)
        self.chart_view.setRenderHint(QPainter.Antialiasing)
        self.update_trash_log()


    def reset(self):
        # 확인 창 표시
        reply = QMessageBox.question(self, '확인', '모든 데이터를 삭제하시겠습니까?', 
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            # 데이터베이스에서 모든 데이터 삭제
            connection = mysql.connector.connect(
                host="database-1.cpwy8c66woni.ap-northeast-2.rds.amazonaws.com",
                port=3306,
                user="admin",
                password="lolmh0211",
                database="DL_project"
            )
            cursor = connection.cursor()
            cursor.execute("DELETE FROM log")  # trash 테이블의 모든 데이터 삭제
            connection.commit()  # 변경 사항 커밋
            connection.close()

            # 차트와 로그 초기화
            self.chart_view.setChart(QChart())
            self.log_text_edit.clear()  # 로그도 초기화

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TrashSortingApp()
    window.show()
    sys.exit(app.exec_())
