import json
import math
import socket
import subprocess
import sys
import zlib
import base64
from time import sleep
import time
import errno
import threading

END_MARKER = '<END>'
BUFFER_SIZE = 131072  # 128 KB

# Nén luồng stream realtime (download SUMO→Unity). Payload JSON rất "phình"; nén raw-DEFLATE
# rồi base64 (text-safe để đi qua framing <END> sẵn có, không cần đổi tầng khung).
# Tiền tố GZ_PREFIX để Unity tự nhận biết gói đã nén; gói không có tiền tố = JSON thường (tương thích ngược).
COMPRESS_DOWNLOAD = True   # cờ bật/tắt nén — đặt False để debug bằng JSON thô.
GZ_PREFIX = 'GZ:'
_COMPRESS_LEVEL = 6        # cân bằng tỉ lệ nén / CPU


def _compress_payload(data_str: str) -> str:
    """JSON string -> 'GZ:' + base64(raw-deflate). Raw deflate (wbits âm) để .NET DeflateStream
    (Unity) giải nén trực tiếp, không cần header zlib/gzip."""
    co = zlib.compressobj(_COMPRESS_LEVEL, zlib.DEFLATED, -zlib.MAX_WBITS)
    comp = co.compress(data_str.encode('utf-8')) + co.flush()
    return GZ_PREFIX + base64.b64encode(comp).decode('ascii')

# Per-socket receive buffers to handle TCP stream framing.
# TCP can coalesce multiple application messages into one recv, so we must
# split on END_MARKER and keep any remainder for the next call.
_recv_buffers = {}
_recv_buffers_lock = threading.Lock()


def _socket_key(sock: socket.socket) -> int:
    try:
        return sock.fileno()
    except Exception:
        return id(sock)


def _recv_next_message(client_socket: socket.socket) -> str:
    """Receive exactly one END_MARKER-terminated message from a TCP stream.

    Returns:
        The message string (without END_MARKER), or "" if the connection was closed.
    """
    key = _socket_key(client_socket)
    with _recv_buffers_lock:
        buffer = _recv_buffers.get(key, "")

    while True:
        marker_index = buffer.find(END_MARKER)
        if marker_index >= 0:
            message = buffer[:marker_index]
            remainder = buffer[marker_index + len(END_MARKER):]
            with _recv_buffers_lock:
                _recv_buffers[key] = remainder
            return message

        data = client_socket.recv(BUFFER_SIZE)
        if not data:
            with _recv_buffers_lock:
                _recv_buffers.pop(key, None)
            return ""

        # Use strict UTF-8 decode; if your payload can contain arbitrary bytes,
        # consider errors='replace'. For JSON/control messages, strict is preferred.
        buffer += data.decode('utf-8')

def send_data(client_socket: socket.socket, data, compress: bool = False) -> bool:
    """Gửi dữ liệu theo cụm. compress=True → nén raw-deflate+base64 (tiền tố GZ:)."""
    try:
        data_str = json.dumps(data)
        if compress:
            data_str = _compress_payload(data_str)
        # Ghép END_MARKER vào payload để tránh phải gửi một gói rời
        data_str = data_str + END_MARKER
        total_size = len(data_str)
        num_packets = math.ceil(total_size / BUFFER_SIZE)

        for i in range(num_packets):
            start = i * BUFFER_SIZE
            end = min(start + BUFFER_SIZE, total_size)
            packet = data_str[start:end]
            client_socket.sendall(packet.encode('utf-8'))
        
        # print(f"Sent data in {num_packets} packet(s), total size: {total_size} bytes")

        return True
    except Exception as e:
        print(f"Error sending data: {e}")
        return False
    
def receive_data(client_socket: socket.socket) :
    """Nhận dữ liệu theo cụm"""
    try:
        return _recv_next_message(client_socket)
    except Exception as e:
        print(f"Error receiving data: {e}")
        return ""

def receive_message(client_socket: socket.socket) :
    """Nhận dữ liệu thô theo cụm"""
    try:
        return _recv_next_message(client_socket)
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
            if client_socket:
                # Tắt Nagle trên kết nối đã chấp nhận: stream realtime nhịp ~50ms cần độ trễ thấp,
                # không để TCP gộp/giữ gói tới ~40ms.
                try:
                    client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                except Exception as e:
                    print(f"[Warn] Could not set TCP_NODELAY: {e}")
            if not client_socket:
                try:
                    print(f"Error accepting connection on server socket: {server_socket} | Address: {server_socket.getsockname()}")
                except Exception as e:
                    print(f"Error accepting connection on server socket: {server_socket} | Could not get address: {e}")
                continue
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