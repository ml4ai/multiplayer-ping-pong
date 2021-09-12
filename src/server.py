import socket
import threading
import pygame
from utils import Network
from utils import Paddle

PORT = 5050
INITIAL_PADDLE_POSITION = 20

class Server:
    def __init__(self):
        host = socket.gethostbyname(socket.gethostname())

        self._server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Reuse socket
        self._server.bind((host, PORT))

        print(f"[NETWORK] ({host}, {PORT})")

        self._currentID = 0
        self._player_positions = {}
        self._client_networks = {}

    def run(self):
        update_clients_thread = threading.Thread(target=self._update_clients)
        update_clients_thread.start()

        self._server.listen()

        while True:
            client_conn, client_addr = self._server.accept()
            client_thread = threading.Thread(target=self._handle_client, args=(client_conn, client_addr))
            client_thread.start()

    def _update_clients(self):
        clock = pygame.time.Clock()
        while True:
            networks = self._client_networks.values()
            for client_network in networks:
                client_network.send(self._player_positions)
            
            clock.tick(60)

    def _handle_client(self, connection, address):
        print("[SERVER] connected to: ", address)
        
        player_id = self._currentID
        self._currentID += 1

        client_network = Network(connection)
        self._client_networks[player_id] = client_network
        client_network.send(player_id)

        self._player_positions[player_id] = [INITIAL_PADDLE_POSITION, 0]

        player = Paddle(INITIAL_PADDLE_POSITION, 0, 800)

        while True:
            try:
                data = client_network.receive()

                if data == 'x':
                    del self._player_positions[player_id]
                    del self._client_networks[player_id]
                    break
                elif data == "UP":
                    self._player_positions[player_id][1] = player.move_up()
                elif data == "DOWN":
                    self._player_positions[player_id][1] = player.move_down()

            except Exception as e:
                print(e)
                continue

        print("Connection lost: ", address)
        connection.close()


if __name__ == "__main__":
    pygame.init()

    server = Server()
    server.run()
