import socket
import threading
from utils import Network

PORT = 5050

class Server:
    def __init__(self):
        host = socket.gethostbyname(socket.gethostname())

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Reuse socket
        self.server.bind((host, PORT))

        print(f"[NETWORK] ({host}, {PORT})")

        self.currentID = 0

    def run(self):
        self.server.listen()

        while True:
            client_conn, client_addr = self.server.accept()
            client_thread = threading.Thread(target=self.handle_client, args=(client_conn, client_addr))
            client_thread.start()

    def handle_client(self, connection, address):
        print("[SERVER] connected to: ", address)
        client_network = Network(connection)

        client_network.send(self.currentID)

        self.currentID += 1

        while True:
            try:
                data = client_network.receive()

                if data == 'x':
                    break

                print(data)
            except socket.error as err:
                print(err)
                break

        print("Connection lost: ", address)
        connection.close()


if __name__ == "__main__":
    server = Server()
    server.run()
