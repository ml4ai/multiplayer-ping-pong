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

PADDLE_Y_CENTER = int((cfg.WINDOW_SIZE[1] - cfg.PADDLE_HEIGHT) / 2)


class Server:
    def __init__(self):
        # Get server's host IPv4 address
        self._host = socket.gethostbyname(socket.gethostname())

        # Establish connection where clients can get game state update
        self._server_subscribe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_subscribe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Reuse socket
        self._server_subscribe.bind((self._host, INCOMING_PORT))

        # Establish connection where clients send control commands
        self._server_publish = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_publish.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Reuse socket
        self._server_publish.bind((self._host, OUTGOING_PORT))

        print(f"[NETWORK] ({self._host}, {INCOMING_PORT})")

        self._currentID = 1
        self._positions = {}
        self._subscribed_networks = []

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
        subscribing_thread = threading.Thread(target=self._dispatch_subscribing_network, daemon=True)
        subscribing_thread.start()

        updating_subscribers_thread = threading.Thread(target=self._update_subscribers, daemon=True)
        updating_subscribers_thread.start()

        publishing_thread = threading.Thread(target=self._dispatch_publishing_network, daemon=True)
        publishing_thread.start()

        server_control_thread = threading.Thread(target=self._server_control, daemon=True)
        server_control_thread.start()

        # Wait for threads to finish
        server_control_thread.join()
        updating_subscribers_thread.join()

        # Create fake connections to close the subscribing and publishing threads
        fake_subscribing_network = Network.from_address(self._host, INCOMING_PORT)
        fake_subscribing_network.close()

        fake_publishing_network = Network.from_address(self._host, OUTGOING_PORT)
        fake_publishing_network.send("LEFT")
        fake_publishing_network.close()

        # Wait for threads to finish
        subscribing_thread.join()
        publishing_thread.join()

    def _dispatch_subscribing_network(self):
        """
        Dispatch client's connection for receiving game state updates from server
        """
        # Listen for client connection
        self._server_subscribe.listen()

        while not self._exit_request:
            client_conn, client_addr = self._server_subscribe.accept()
            client_network = Network(client_conn)

            # Add client connection to list for sending game state update
            self._subscribed_networks.append(client_network)

    def _dispatch_publishing_network(self):
        """
        Establish connection to receive clients' command
        """
        # Listen for client connection
        self._server_publish.listen()

        while not self._exit_request:
            client_conn, client_addr = self._server_publish.accept()
            client_network = Network(client_conn)

            # Clients specify what team they want to be on
            data = client_network.receive()

            # Left team
            if data == "LEFT":
                self._positions[self._currentID] = [PADDLE_X_LEFT, PADDLE_Y_CENTER]
            # Right team
            else:
                self._positions[self._currentID] = [PADDLE_X_RIGHT, PADDLE_Y_CENTER]

            # Create a thread for receiving client's commands
            client_thread = threading.Thread(target=self._handle_publisher, args=(client_network, self._currentID))
            client_thread.start()

            self._currentID += 1

    def _update_subscribers(self):
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
            data["score_left"] = self._score_left
            data["score_right"] = self._score_right
            data["positions"] = self._positions
            data["exit_request"] = False

            removing_indexes = []
            for index, client_update_network in enumerate(self._subscribed_networks):
                try:
                    # Send game state update to client
                    client_update_network.send(data)
                except Exception as e:
                    # Mark client connection for removal when client disconnects
                    removing_indexes.append(index)

            # Remove disconnected clients from the game
            offset = 0
            for index in removing_indexes:
                self._subscribed_networks[index - offset].close()
                del self._subscribed_networks[index - offset]
                offset += 1
                print("Connection closed")
            
            # Limit loop rate to 120 loops per second
            clock.tick(120)

        for client_update_network in self._subscribed_networks:
            data["exit_request"] = True
            client_update_network.send(data)
            client_update_network.close()

        # Close server connection
        self._server_subscribe.close()
        self._server_publish.close()

    def _handle_publisher(self, client_control_network, client_id):
        """
        Update game state with client's command
        """
        # Initialize client's paddle
        player_paddle = Paddle(self._positions[client_id], 0, cfg.WINDOW_SIZE[1] - cfg.PADDLE_HEIGHT)
        self._thread_lock.acquire()
        self._paddles[client_id] = player_paddle
        self._thread_lock.release()

        # Notify client its paddle id
        client_control_network.send(client_id)

        while not self._exit_request:
            try:
                # Get command from client
                command = client_control_network.receive()

                # Client exits
                if command == 'x':
                    del self._positions[client_id]
                    self._thread_lock.acquire()
                    del self._paddles[client_id]
                    self._thread_lock.release()
                    break

                # Client moves paddle up
                elif not self._game_paused and command == "UP":
                    self._positions[client_id][1] = player_paddle.move_up()

                # Client moves paddle down
                elif not self._game_paused and command == "DOWN":
                    self._positions[client_id][1] = player_paddle.move_down()

            except Exception as e:
                # Remove client's paddle from the game
                self._thread_lock.acquire()
                del self._paddles[client_id]
                self._thread_lock.release()
                break

        client_control_network.close()

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

    server = Server()
    server.run()
