import socket
import threading
import pygame
import config as cfg
from utils import Network
from utils import Paddle
from utils import Ball

INCOMING_PORT = cfg.SERVER_PORT
OUTGOING_PORT = INCOMING_PORT + 1

PADDLE_X_LEFT = 0
PADDLE_X_RIGHT = cfg.WINDOW_SIZE[0] - cfg.PADDLE_WIDTH


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

        self._score_left = 0
        self._score_right = 0

        self._thread_lock = threading.Lock()

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
            self._ball.update()

            self._thread_lock.acquire()
            for paddle in self._paddles.values():
                if pygame.sprite.collide_mask(self._ball, paddle):
                    self._ball.bounce(int(((self._ball.rect.y + cfg.BALL_SIZE / 2.0) - (paddle.rect.y + cfg.PADDLE_HEIGHT / 2.0)) * 0.15))
                    break
            self._thread_lock.release()

            if self._ball.rect.x >= cfg.WINDOW_SIZE[0] - cfg.BALL_SIZE:
                self._score_left += 1
                self._ball.bounce()
                self._ball.rect.x -= 10
            if self._ball.rect.x <= 0:
                self._score_right += 1
                self._ball.bounce()
                self._ball.rect.x += 10
            if self._ball.rect.y >= cfg.WINDOW_SIZE[1] - cfg.BALL_SIZE:
                self._ball.velocity[1] = -self._ball.velocity[1]
            if self._ball.rect.y <= 0:
                self._ball.velocity[1] = -self._ball.velocity[1]

            self._positions[0] = [self._ball.rect.x, self._ball.rect.y]

            data = {}
            data["score_left"] = self._score_left
            data["score_right"] = self._score_right
            data["positions"] = self._positions

            removing_indexes = []
            for index, client_update_network in enumerate(self._subscribed_networks):
                try:
                    client_update_network.send(data)
                except Exception as e:
                    print(e)
                    removing_indexes.append(index)

            offset = 0
            for index in removing_indexes:
                self._subscribed_networks[index - offset].close()
                del self._subscribed_networks[index - offset]
                offset += 1
                print("Connection closed")
            
            clock.tick(120)

    def _handle_publisher(self, client_control_network, client_id):
        player_paddle = Paddle(self._positions[client_id][0], 0, 700)
        self._thread_lock.acquire()
        self._paddles[client_id] = player_paddle
        self._thread_lock.release()

        client_control_network.send(client_id)

        while True:
            try:
                data = client_control_network.receive()

                if data == 'x':
                    del self._positions[client_id]
                    self._thread_lock.acquire()
                    del self._paddles[client_id]
                    self._thread_lock.release()
                    break
                elif data == "UP":
                    self._positions[client_id][1] = player_paddle.move_up()
                elif data == "DOWN":
                    self._positions[client_id][1] = player_paddle.move_down()

            except Exception as e:
                print(e)
                self._thread_lock.acquire()
                del self._paddles[client_id]
                self._thread_lock.release()
                break

        print("Connection closed")
        client_control_network.close()


if __name__ == "__main__":
    pygame.init()

    server = Server()
    server.run()
