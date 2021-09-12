import socket
import json

HEADER = 64

class Network:
    def __init__(self, connection: socket.socket):
        self.connection = connection

    @classmethod
    def from_address(cls, host: str, port: int):
        connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        connection.connect((host, port))

        return cls(connection)

    def send(self, data):
        data_msg = json.dumps(data).encode()
        len_msg = str(len(data_msg)).encode()
        len_msg += b' ' * (HEADER - len(len_msg))
        self.connection.send(len_msg)
        self.connection.send(data_msg)

    def receive(self):
        msg_len = self.connection.recv(HEADER).decode()

        if not msg_len:
            return None

        return json.loads(self.connection.recv(int(msg_len)).decode())
