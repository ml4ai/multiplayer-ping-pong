import pygame
import sys
import threading
import socket
from select import select
import json
from utils import send
import config as cfg


class AIClient:
    def __init__(self):
        host = sys.argv[1]
        port = int(sys.argv[2])

        self._team = sys.argv[3]

        self._client_id = -1

        # Monitor paddle's and ball's position
        self._ball_position = [0, 0]
        self._paddle_position = [0, 0]

        # Establish two-channel connection to server
        self._from_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._from_server.connect((host, port))
        self._from_server.setblocking(False)

        self._to_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._to_server.connect((host, port + 1))
        self._to_server.setblocking(False)

        readable, _, _ = select([self._to_server], [], [self._to_server])
        if readable:
            self._client_id = int(readable[0].recv(cfg.HEADER).decode('utf-8'))
        else:
            raise RuntimeError("Fail to establish connection with server")

        print("Connected to server, paddle ID: " + str(self._client_id))

        self._running = True

    def run(self):
        """
        Run ping pong on client's side
        """
        # Create a thread for sending client input to server
        control_thread = threading.Thread(target=self._send_input, daemon=True)
        control_thread.start()
        
        # Create a thread for controlling client from terminal
        client_control_thread = threading.Thread(target=self._client_control, daemon=True)
        client_control_thread.start()

        while self._running:
            # Get update from server about the state of the game
            readable, _, _ = select([self._from_server], [], [self._from_server])
            if readable:
                message = readable[0].recv(cfg.HEADER)

                if not message:
                    continue

                data = json.loads(message.decode('utf-8'))

                # Exit game when server is closed
                if data["message_type"] == "command":
                    if data["message"] == "CLOSE":
                        self._running = False
                        print("Server closed")
                        break
            else:
                self._running = False
                print("Server closed")
                break

            for object_id, position in data["positions"].items():
                # The ball's position is at index 0
                if int(object_id) == 0:
                    self._ball_position = position
                # Get AI's paddle's location
                elif int(object_id) == self._client_id:
                    self._paddle_position = position

        control_thread.join()
        client_control_thread.join()

    def _send_input(self):
        """
        Send AI's input command to server
        """
        # Notify server the team the client wants to be on
        _, writable, _ = select([], [self._to_server], [self._to_server])
        if writable:
            send(writable[0], self._team)
        else:
            raise RuntimeError("Lost connection with server")

        clock = pygame.time.Clock() # Control the rate of sending data to server
        while self._running:
            # Send control commands to server
            # Note that positions specify the location of the top left corners of the sprites

            # Go up when the ball is above the paddle
            if (self._ball_position[1] + cfg.BALL_SIZE / 2.0) - (self._paddle_position[1] + cfg.PADDLE_HEIGHT / 2.0) < 10:
                _, writable, _ = select([], [self._to_server], [self._to_server])
                if writable:
                    try:
                        send(writable[0], "UP")
                    except BrokenPipeError:
                        print("Server closed")
                        self._running = False

            # Go down when the ball is below the paddle
            elif (self._ball_position[1] + cfg.BALL_SIZE / 2.0) - (self._paddle_position[1] + cfg.PADDLE_HEIGHT / 2.0) > 10:
                _, writable, _ = select([], [self._to_server], [self._to_server])
                if writable:
                    try:
                        send(writable[0], "DOWN")
                    except BrokenPipeError:
                        print("Server closed")
                        self._running = False
            
            # Limit loop rate to 120 loops per second
            clock.tick(120)

    def _client_control(self):
        """
        Control client
        """
        while self._running:
            readable, _, _ = select([sys.stdin], [], [], 0.5)

            if not readable:
                continue

            command = readable[0].readline().strip()
            
            if command == "exit":
                self._running = False
                _, writable, _ = select([], [self._to_server], [self._to_server], 0.1)
                if writable:
                    try:
                        send(writable[0], "CLOSE")
                    except BrokenPipeError:
                        print("Server closed")
            else:
                print("Unknown command")


if __name__ == "__main__":
    pygame.init()

    ai_client = AIClient()
    ai_client.run()
