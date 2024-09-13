import cv2
import socket
import struct
import pickle
from ultralytics import YOLO

# YOLO 모델 로드
model = YOLO("/home/jun/dev_ws/yolov5/yolov8n.pt")

# 서버 설정
server_ip = '192.168.0.214'  # 서버의 실제 IP 주소
server_port = 22223

# 소켓 생성 및 서버에 연결
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    client_socket.connect((server_ip, server_port))
except Exception as e:
    print(f"서버에 연결할 수 없습니다: {e}")
    exit()

while True:
    try:
        # 데이터 크기 수신
        data_size_bytes = client_socket.recv(struct.calcsize('L'))
        if not data_size_bytes:
            print("서버와의 연결이 끊어졌습니다.")
            break
        
        data_size = struct.unpack('L', data_size_bytes)[0]

        # 데이터 수신
        data = b''
        while len(data) < data_size:
            packet = client_socket.recv(data_size - len(data))
            if not packet:
                print("서버와의 연결이 끊어졌습니다.")
                break
            data += packet

        # 데이터 디코딩
        frame = pickle.loads(data)
        results = model(frame)
        result_frame = results

        # YOLO 결과를 pickle로 직렬화
        result_data = pickle.dumps(result_frame)
        result_data_size = len(result_data)
        
        # YOLO 결과 크기 전송
        client_socket.sendall(struct.pack('L', result_data_size))
        # YOLO 결과 전송
        client_socket.sendall(result_data)

    except Exception as e:
        print(f"오류 발생: {e}")
        break

# 자원 해제
client_socket.close()