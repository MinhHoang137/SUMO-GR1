import json
import math
import socket
import subprocess
import sys
from time import sleep
import time
import errno
import threading

END_MARKER = '<END>'
BUFFER_SIZE = 131072  # 128 KB

def send_data(client_socket: socket.socket, data) -> bool:
    """Gửi dữ liệu theo cụm"""
    try:
        data_str = json.dumps(data)
        total_size = len(data_str)
        num_packets = math.ceil(total_size / BUFFER_SIZE)

        print(f"Sending {num_packets} packets...")

        for i in range(num_packets):
            start = i * BUFFER_SIZE
            end = min(start + BUFFER_SIZE, total_size)
            packet = data_str[start:end]
            client_socket.sendall(packet.encode('utf-8'))

        # Gửi thông báo kết thúc
        client_socket.sendall(END_MARKER.encode('utf-8'))

        return True
    except Exception as e:
        print(f"Error sending data: {e}")
        return False
    
def receive_data(client_socket: socket.socket) :
    """Nhận dữ liệu theo cụm"""
    try:
        full_data = ''
        while True:
            data = client_socket.recv(BUFFER_SIZE)
            if not data:
                break
            text = data.decode('utf-8')
            full_data += text
            if END_MARKER in full_data:
                full_data = full_data.replace(END_MARKER, '')
                break
        data = json.loads(full_data)
        return full_data
    except Exception as e:
        print(f"Error receiving data: {e}")
        return ""

def receive_message(client_socket: socket.socket) :
    """Nhận dữ liệu thô theo cụm"""
    try:
        full_data = ''
        while True:
            data = client_socket.recv(BUFFER_SIZE)
            if not data:
                break
            text = data.decode('utf-8')
            full_data += text
            if END_MARKER in full_data:
                full_data = full_data.replace(END_MARKER, '')
                break
        return full_data
    except Exception as e:
        print(f"Error receiving data: {e}")
        return None 

def async_task(target, *args, join=False, daemon=False):
    thread = threading.Thread(target=target, args=args)
    thread.daemon = daemon  # nếu True thì thread không ngăn tiến trình chính thoát
    thread.start()
    if join:
        thread.join()
    return thread

def create_server_socket(host: str, port: int) -> socket.socket:
    """Tạo socket server"""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(10)
    print(f"Server listening on {host}:{port}...")
    return server_socket

def server_thread(server_socket: socket.socket, client_handler):
    """Luồng server để nhận dữ liệu"""
    while True:
        try:
            client_socket, addr = server_socket.accept()
            # tạo luồng client handler không phải daemon để cho phép shutdown gọn
            async_task(client_handler, client_socket, daemon=False)
        except Exception as e:
            # If the server socket was closed, stop the loop and exit the thread
            winerr = getattr(e, 'winerror', None)
            errnum = getattr(e, 'errno', None)
            if winerr == 10038 or errnum == errno.EBADF or (hasattr(server_socket, 'fileno') and server_socket.fileno() < 0):
                print("Server socket closed, exiting server thread.")
                break
            print(f"Error in server thread: {e}")
            time.sleep(0.5)
            continue