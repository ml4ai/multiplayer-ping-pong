import socket
import json
import sys

HEADER = 2048 # The amount of bytes expect to receive

class Network:
    def __init__(self, connection: socket.socket):
        self.connection = connection

    @classmethod
    def from_address(cls, host: str, port: int):
        """
        Connect to a specific IPv4 address (host) and port
        """
        connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        connection.setblocking(False)
        connection.settimeout(0.5)

        connection.connect((host, port))

        return cls(connection)

    def close(self):
        self.connection.close()

    def send(self, data):
        # Convert data into json string and encode it
        data_msg = json.dumps(data).encode('utf-8')

        # Pad the json string to specific data legnth
        data_msg += b' ' * (HEADER - len(data_msg))

        # Send data
        self.connection.sendall(data_msg)

    def receive(self):
        data = None
        while True:
            # Receive the first data
            if data is None:
                data = self.connection.recv(HEADER)

            # Append the next data
            else:
                data += self.connection.recv(HEADER)

            # If data has been received in full, return data
            size = sys.getsizeof(data)
            if size == HEADER + 33:
                return json.loads(data.decode('utf-8'))

            # Faulty data (data longer than expected data length)
            # reset and collect new data
            elif size > HEADER + 33:
                data = None
