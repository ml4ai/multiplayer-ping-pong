import socket
import json
import sys

HEADER = 2048

class Network:
    def __init__(self, connection: socket.socket):
        self.connection = connection

    @classmethod
    def from_address(cls, host: str, port: int):
        connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        connection.connect((host, port))

        return cls(connection)

    def close(self):
        self.connection.close()

    def send(self, data):
        data_msg = json.dumps(data).encode('utf-8')
        data_msg += b' ' * (HEADER - len(data_msg))
        self.connection.sendall(data_msg)

    def receive(self):
        data = None
        while True:
            if data is None:
                data = self.connection.recv(HEADER)
            else:
                data += self.connection.recv(HEADER)

            size = sys.getsizeof(data)
            if size == 2081:
                return json.loads(data.decode('utf-8'))
            elif size > 2081:
                data = None
