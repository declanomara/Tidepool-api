import socket
import json


def gather_stats():
    HOST = "127.0.0.1"  # The server's hostname or IP address
    PORT = 65001  # The port used by the server

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        s.sendall(b"Hello, world")
        data = s.recv(1024).decode('utf-8')

    return json.loads(data)