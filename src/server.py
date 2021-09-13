import socket
import threading
import pygame
from utils import Network
from utils import Paddle
from utils import Ball

INCOMING_PORT = 5050
OUTGOING_PORT = INCOMING_PORT + 1
PADDLE_X_LEFT = 0
PADDLE_X_RIGHT = 1080

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

        self._currentID = 1
        self._positions = {}
        self._subscribed_networks = []

        self._ball = Ball()
        self._positions[0] = [self._ball.rect.x, self._ball.rect.y]

        self._paddles = {}

        self._all_sprites_list = pygame.sprite.Group()
        self._all_sprites_list.add(self._ball)

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

            data = client_network.receive()
            if data == "LEFT":
                self._positions[self._currentID] = [PADDLE_X_LEFT, 0]
            else:
                self._positions[self._currentID] = [PADDLE_X_RIGHT, 0]

            print("[SERVER] publish to: ", client_addr)

            client_thread = threading.Thread(target=self._handle_publisher, args=(client_network, self._currentID))
            client_thread.start()

            self._currentID += 1

    def _update_subscribers(self):
        clock = pygame.time.Clock()
        while True:
            self._all_sprites_list.update()
            for _, paddle in self._paddles.items():
                if pygame.sprite.collide_mask(self._ball, paddle):
                    self._ball.bounce()
                    break

            if self._ball.rect.x >= 1090:
                self._ball.velocity[0] = -self._ball.velocity[0]
            if self._ball.rect.x <= 0:
                self._ball.velocity[0] = -self._ball.velocity[0]
            if self._ball.rect.y >= 790:
                self._ball.velocity[1] = -self._ball.velocity[1]
            if self._ball.rect.y <= 0:
                self._ball.velocity[1] = -self._ball.velocity[1]

            self._positions[0] = [self._ball.rect.x, self._ball.rect.y]

            removing_indexes = []
            for index, client_update_network in enumerate(self._subscribed_networks):
                try:
                    client_update_network.send(self._positions)
                except Exception as e:
                    print(e)
                    removing_indexes.append(index)

            offset = 0
            for index in removing_indexes:
                self._subscribed_networks[index - offset].close()
                del self._subscribed_networks[index - offset]
                offset += 1
            
            clock.tick(120)

    def _handle_publisher(self, client_control_network, client_id):
        player_paddle = Paddle(self._positions[client_id][0], 0, 700)
        self._paddles[client_id] = player_paddle
        self._all_sprites_list.add(player_paddle)

        while True:
            try:
                data = client_control_network.receive()

                if data == 'x':
                    del self._positions[client_id]
                    self._all_sprites_list.remove(player_paddle)
                    del self._paddles[client_id]
                    break
                elif data == "UP":
                    self._positions[client_id][1] = player_paddle.move_up()
                elif data == "DOWN":
                    self._positions[client_id][1] = player_paddle.move_down()

            except Exception as e:
                print(e)
                self._all_sprites_list.remove(player_paddle)
                break

        print("Connection closed")
        client_control_network.close()


if __name__ == "__main__":
    pygame.init()

    server = Server()
    server.run()
