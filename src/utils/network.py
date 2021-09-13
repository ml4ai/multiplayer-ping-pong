import socket
import json

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
        data_msg = json.dumps(data).encode()
        data_msg += b' ' * (HEADER - len(data_msg))
        self.connection.send(data_msg)

    def receive(self):
        data = self.connection.recv(HEADER)

        if data:
            return json.loads(data.decode())
        else:
            return None
