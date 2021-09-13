import socket
import threading
import pygame
from utils import Network
from utils import Paddle

INCOMING_PORT = 5050
OUTGOING_PORT = INCOMING_PORT + 1
INITIAL_PADDLE_POSITION = 20

class Server:
    def __init__(self):
        host = socket.gethostbyname(socket.gethostname())

        self._server_subscribe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_subscribe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Reuse socket
        self._server_subscribe.bind((host, INCOMING_PORT))

        self._server_publish = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_publish.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Reuse socket
        self._server_publish.bind((host, OUTGOING_PORT))

        print(f"[NETWORK] ({host}, {INCOMING_PORT})")

        self._currentID = 0
        self._paddle_positions = {}
        self._subscribed_networks = []

    def run(self):
        subscribing_thread = threading.Thread(target=self._dispatch_subscribing_network)
        subscribing_thread.start()

        updating_subscribers_thread = threading.Thread(target=self._update_subscribers)
        updating_subscribers_thread.start()

        publishing_thread = threading.Thread(target=self._dispatch_publishing_network)
        publishing_thread.start()

        subscribing_thread.join()
        updating_subscribers_thread.join()
        publishing_thread.join()

    def _dispatch_subscribing_network(self):
        self._server_subscribe.listen()

        while True:
            client_conn, client_addr = self._server_subscribe.accept()
            client_network = Network(client_conn)

            self._subscribed_networks.append(client_network)

            print("[SERVER] subscribed: ", client_addr)

    def _dispatch_publishing_network(self):
        self._server_publish.listen()

        while True:
            client_conn, client_addr = self._server_publish.accept()
            client_network = Network(client_conn)

            self._paddle_positions[self._currentID] = [INITIAL_PADDLE_POSITION, 0]

            print("[SERVER] publish to: ", client_addr)

            client_thread = threading.Thread(target=self._handle_publisher, args=(client_network, self._currentID))
            client_thread.start()

            self._currentID += 1

    def _update_subscribers(self):
        clock = pygame.time.Clock()
        while True:
            removing_indexes = []
            for index, client_update_network in enumerate(self._subscribed_networks):
                try:
                    client_update_network.send(self._paddle_positions)
                except Exception as e:
                    print(e)
                    removing_indexes.append(index)

            offset = 0
            for index in removing_indexes:
                self._subscribed_networks[index - offset].close()
                del self._subscribed_networks[index - offset]
                offset += 1
            
            clock.tick(60)

    def _handle_publisher(self, client_control_network, client_id):
        player = Paddle(INITIAL_PADDLE_POSITION, 0, 800)

        while True:
            try:
                data = client_control_network.receive()

                if data == 'x':
                    del self._paddle_positions[client_id]
                    break
                elif data == "UP":
                    self._paddle_positions[client_id][1] = player.move_up()
                elif data == "DOWN":
                    self._paddle_positions[client_id][1] = player.move_down()

            except Exception as e:
                print(e)
                continue

        print("Connection closed")
        client_control_network.close()


if __name__ == "__main__":
    pygame.init()

    server = Server()
    server.run()
