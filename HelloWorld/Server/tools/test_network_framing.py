import socket
import threading
import time

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import network


HOST, PORT = "127.0.0.1", 5099
msgs: list[str] = []


def handler(client_socket: socket.socket):
    with client_socket:
        msgs.append(network.receive_message(client_socket))
        msgs.append(network.receive_message(client_socket))


def main() -> None:
    server_socket = network.create_server_socket(HOST, PORT)
    t = threading.Thread(target=network.server_thread, args=(server_socket, handler), daemon=True)
    t.start()

    time.sleep(0.1)

    with socket.create_connection((HOST, PORT)) as c:
        payload = '"one"' + network.END_MARKER + '"two"' + network.END_MARKER
        c.sendall(payload.encode("utf-8"))

    time.sleep(0.2)
    print(msgs)

    server_socket.close()


if __name__ == "__main__":
    main()
