import socket
import threading
import pygame
import sys
import json
from select import select
import config as cfg
from utils import Paddle
from utils import Ball
from utils import send

PADDLE_X_LEFT = 0
PADDLE_X_RIGHT = cfg.WINDOW_SIZE[0] - cfg.PADDLE_WIDTH

PADDLE_Y_CENTER = int((cfg.WINDOW_SIZE[1] - cfg.PADDLE_HEIGHT) / 2)


class Server:
    def __init__(self, host: str, port: int):
        # Get server's host IPv4 address
        self._host = host
        self._port = port

        self._to_client_connections = []
        self._from_client_connections = {}

        # Establish connection where clients can get game state update
        self._to_client_request = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._to_client_request.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Reuse socket
        self._to_client_request.bind((self._host, self._port))
        self._to_client_request.setblocking(False)

        # Establish connection where clients send control commands
        self._from_client_request = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._from_client_request.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Reuse socket
        self._from_client_request.bind((self._host, self._port + 1))
        self._from_client_request.setblocking(False)

        print(f"[NETWORK] ({self._host}, {self._port})")

        self._currentID = 1
        self._positions = {}

        self._ball = Ball()
        self._positions[0] = [self._ball.rect.x, self._ball.rect.y]

        self._paddles = {}

        self._score_left = 0
        self._score_right = 0

        self._game_paused = True
        self._exit_request = False

        self._thread_lock = threading.Lock()

    def run(self):
        """
        Set up threads for handling connections
        """
        to_client_request_thread = threading.Thread(target=self._dispatch_to_client_request, daemon=True)
        to_client_request_thread.start()

        from_client_request_thread = threading.Thread(target=self._dispatch_from_client_request, daemon=True)
        from_client_request_thread.start()

        from_client_commands_thread = threading.Thread(target=self._from_client_commands, daemon=True)
        from_client_commands_thread.start()

        to_client_update_state_thread = threading.Thread(target=self._to_client_update_state, daemon=True)
        to_client_update_state_thread.start()

        server_control_thread = threading.Thread(target=self._server_control, daemon=True)
        server_control_thread.start()

        # Wait for threads to finish
        server_control_thread.join()
        to_client_update_state_thread.join()
        to_client_request_thread.join()
        from_client_request_thread.join()
        from_client_commands_thread.join()

        # Close server connection
        self._to_client_request.close()
        self._from_client_request.close()

    def _dispatch_to_client_request(self):
        """
        Dispatch client's connection for receiving game state updates from server
        """
        # Listen for client connection
        self._to_client_request.listen()

        while not self._exit_request:
            readable, _, _ = select([self._to_client_request], [], [self._to_client_request], 0.1)
            if readable:
                client_conn, client_addr = readable[0].accept()
                client_conn.setblocking(False)
                self._to_client_connections.append(client_conn)
                print("Sending replies to [" + client_addr[0] + ", " + str(client_addr[1]) + ']')

    def _dispatch_from_client_request(self):
        """
        Establish connection to receive clients' command
        """
        # Listen for client connection
        self._from_client_request.listen()

        while not self._exit_request:
            readable, _, _ = select([self._from_client_request], [], [self._from_client_request], 0.1)

            if readable:
                client_conn, client_addr = readable[0].accept()
                client_conn.setblocking(False)

                _, writable, _ = select([], [client_conn], [client_conn])
                try:
                    send(writable[0], self._currentID)
                except BrokenPipeError:
                    print("Connection closed")
                    continue

                self._thread_lock.acquire()
                self._from_client_connections[client_conn] = self._currentID
                self._positions[self._currentID] = [PADDLE_X_LEFT, PADDLE_Y_CENTER]
                self._paddles[self._currentID] = Paddle(self._positions[self._currentID], 0, cfg.WINDOW_SIZE[1] - cfg.PADDLE_HEIGHT)
                self._thread_lock.release()

                print("Receiving commands from [" + str(self._currentID) + ", " + client_addr[0] + ", " + str(client_addr[1]) + ']')

                self._currentID += 1

    def _to_client_update_state(self):
        """
        Update game state then send game state updates to clients
        """
        clock = pygame.time.Clock() # Control the rate of sending data to clients
        while not self._exit_request:
            if not self._game_paused:

                # Update state of the ball
                self._ball.update()

                # Check for collision between
                paddle_collide_ball = False
                self._thread_lock.acquire()
                for paddle in self._paddles.values():
                    if pygame.sprite.collide_mask(self._ball, paddle):
                        self._ball.bounce(int(((self._ball.rect.y + cfg.BALL_SIZE / 2.0) - (paddle.rect.y + cfg.PADDLE_HEIGHT / 2.0)) * 0.15))
                        
                        if self._ball.rect.x < cfg.WINDOW_SIZE[0] / 2:
                            self._ball.rect.x = cfg.PADDLE_WIDTH

                        else:
                            self._ball.rect.x = cfg.WINDOW_SIZE[0] - cfg.PADDLE_WIDTH - cfg.BALL_SIZE

                        paddle_collide_ball = True
                        break
                self._thread_lock.release()

                # If ball has not collided with paddle, check if it collides with the wall
                if not paddle_collide_ball:
                    # Collides with right wall
                    if self._ball.rect.x >= cfg.WINDOW_SIZE[0] - cfg.BALL_SIZE:
                        self._score_left += 1
                        self._ball.bounce()
                        # Offset the ball to avoid collision with paddle
                        self._ball.rect.x = cfg.WINDOW_SIZE[0] - cfg.BALL_SIZE

                    # Collides left wall
                    elif self._ball.rect.x <= 0:
                        self._score_right += 1
                        self._ball.bounce()
                        # Offset the ball to avoid collision with paddle
                        self._ball.rect.x = 0

                    # Collides with bottom wall
                    elif self._ball.rect.y >= cfg.WINDOW_SIZE[1] - cfg.BALL_SIZE:
                        self._ball.rect.y = cfg.WINDOW_SIZE[1] - cfg.BALL_SIZE - 1
                        self._ball.velocity[1] = -self._ball.velocity[1]

                    # Collides with top wall
                    elif self._ball.rect.y <= 0:
                        self._ball.rect.y = 1
                        self._ball.velocity[1] = -self._ball.velocity[1]

                # Store game state
                self._positions[0] = [self._ball.rect.x, self._ball.rect.y]

            data = {}
            data["message_type"] = "state"
            data["score_left"] = self._score_left
            data["score_right"] = self._score_right
            data["positions"] = self._positions

            _, writable, exceptional = select([], self._to_client_connections, self._to_client_connections, 0)
            for connection in writable:
                try:
                    send(connection, data)
                except:
                    print("Connection closed")
                    connection.close()
                    self._to_client_connections.remove(connection)
            
            for connection in exceptional:
                connection.close()
                self._to_client_connections.remove(connection)
            
            # Limit loop rate to 120 loops per second
            if self._game_paused:
                clock.tick(2)
            else:
                clock.tick(120)

        while self._to_client_connections:
            _, writable, exceptional = select([], self._to_client_connections, self._to_client_connections)

            for connection in writable:
                data = {}
                data["message_type"] = "command"
                data["message"] = "CLOSE"

                try:
                    send(connection, data)
                except BrokenPipeError:
                    print("Connection closed")

                connection.close()
                self._to_client_connections.remove(connection)
            
            for connection in exceptional:
                connection.close()
                self._to_client_connections.remove(connection)
            
            clock.tick(120)

    def _from_client_commands(self):
        """
        Handle clients' commands
        """
        while not self._exit_request:
            readable, _, exceptional = select(self._from_client_connections.keys(), [], self._from_client_connections.keys(), 0.2)

            for connection in readable:
                client_id = self._from_client_connections[connection]

                message = connection.recv(cfg.HEADER)

                if not message:
                    continue

                try:
                    command = json.loads(message.decode('utf-8'))
                except json.decoder.JSONDecodeError as err:
                    print(err)
                    continue

                if command == "LEFT":
                    self._positions[client_id] = [PADDLE_X_LEFT, PADDLE_Y_CENTER]
                    self._paddles[client_id].rect.x = PADDLE_X_LEFT
                    self._paddles[client_id].rect.y = PADDLE_Y_CENTER
                elif command == "RIGHT":
                    self._positions[client_id] = [PADDLE_X_RIGHT, PADDLE_Y_CENTER]
                    self._paddles[client_id].rect.x = PADDLE_X_RIGHT
                    self._paddles[client_id].rect.y = PADDLE_Y_CENTER
                elif not self._game_paused and command == "UP":
                    self._positions[client_id][1] = self._paddles[client_id].move_up()
                elif not self._game_paused and command == "DOWN":
                    self._positions[client_id][1] = self._paddles[client_id].move_down()
                elif command == "CLOSE":
                    connection.close()
                    self._thread_lock.acquire()
                    del self._from_client_connections[connection]
                    del self._positions[client_id]
                    del self._paddles[client_id]
                    self._thread_lock.release()

            for connection in exceptional:
                connection.close()
                self._thread_lock.acquire()
                del self._from_client_connections[connection]
                del self._positions[client_id]
                del self._paddles[client_id]
                self._thread_lock.release()

        for connection in self._from_client_connections:
            connection.close()

    def _server_control(self):
        """
        Control the server 
        """
        while not self._exit_request:
            command = input()
            
            if command == "h" or command == "help":
                print("-----")
                print("pause: Pause the game")
                print("unpause: Unpause the game")
                print("restart: Reset game and pause")
                print("exit: Close the server")
                print("h or help: List available commands")
                print("-----")

            elif command == "pause":
                self._game_paused = True

            elif command == "unpause":
                self._game_paused = False

            elif command == "restart":
                self._game_paused = True
                self._score_left = 0
                self._score_right = 0

                self._ball.reset_center()

                for id in self._positions.keys():
                    if id == 0:
                        self._positions[id] = [self._ball.rect.x, self._ball.rect.y]
                    else:
                        self._positions[id][1] = PADDLE_Y_CENTER

            elif command == "exit":
                self._exit_request = True

            else:
                print("Unknown command")


if __name__ == "__main__":
    pygame.init()

    assert len(sys.argv) >= 2

    host = sys.argv[1]
    port = 6060 if len(sys.argv) < 3 else int(sys.argv[2])

    server = Server(host, port)
    server.run()
