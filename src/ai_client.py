import pygame
import sys
import threading
import socket
from select import select
import json
from utils import send
import config as cfg

if len(sys.argv) < 6:
    raise RuntimeError(f"Not enough arguments, {len(sys.argv)}")
elif sys.argv[5] == "SINGLE":
    import config_single as cfg_team
elif sys.argv[5] == "TEAM":
    import config_team as cfg_team
else:
    raise RuntimeError("Must specify SINGLE or TEAM")


class AIClient:
    def __init__(self):
        host = sys.argv[1]
        port = int(sys.argv[2])

        self._team = sys.argv[3]

        self._player_name = sys.argv[4]

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

        _, writable, _ = select([], [self._to_server], [self._to_server])
        try:
            send(writable[0], self._player_name)
        except BrokenPipeError:
            raise RuntimeError("Fail to establish connection with server")

        print("Connected to server, paddle ID: " + self._player_name)

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

                try:
                    data = json.loads(message.decode('utf-8'))
                except json.decoder.JSONDecodeError as err:
                    print(err)
                    continue

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

            for name, position in data["positions"].items():
                # The ball's position is at index 0
                if name == "ball":
                    self._ball_position = position
                # Get AI's paddle's location
                elif name == self._player_name:
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
            if (self._ball_position[1] + cfg_team.BALL_SIZE / 2.0) - (self._paddle_position[1] + cfg_team.PADDLE_HEIGHT / 2.0) < 10:
                _, writable, _ = select([], [self._to_server], [self._to_server])
                if writable:
                    try:
                        send(writable[0], "UP")
                    except BrokenPipeError:
                        print("Server closed")
                        self._running = False

            # Go down when the ball is below the paddle
            elif (self._ball_position[1] + cfg_team.BALL_SIZE / 2.0) - (self._paddle_position[1] + cfg_team.PADDLE_HEIGHT / 2.0) > 10:
                _, writable, _ = select([], [self._to_server], [self._to_server])
                if writable:
                    try:
                        send(writable[0], "DOWN")
                    except BrokenPipeError:
                        print("Server closed")
                        self._running = False
            
            # Limit loop rate to 60 loops per second
            clock.tick(60)

    def _client_control(self):
        """
        Control client
        """
        while self._running:
            readable, _, _ = select([sys.stdin], [], [], 0.5)

            if not readable:
                continue

            command = readable[0].readline().strip()
            
            if command == "h" or command == "help":
                print("-----")
                print("left: Change to left team")
                print("right: Change to right team")
                print("exit: Close the game")
                print("h or help: List available commands")
                print("-----")
            elif command == "exit":
                self._running = False
                _, writable, _ = select([], [self._to_server], [self._to_server], 1.0)
                if writable:
                    try:
                        send(writable[0], "CLOSE")
                    except BrokenPipeError:
                        print("Server closed")
            elif command == "left":
                _, writable, _ = select([], [self._to_server], [self._to_server], 1.0)
                if writable:
                    try:
                        send(writable[0], "LEFT")
                    except BrokenPipeError:
                        print("Server closed")
            elif command == "right":
                _, writable, _ = select([], [self._to_server], [self._to_server], 1.0)
                if writable:
                    try:
                        send(writable[0], "RIGHT")
                    except BrokenPipeError:
                        print("Server closed")
            else:
                print("Unknown command")


if __name__ == "__main__":
    pygame.init()

    ai_client = AIClient()
    ai_client.run()
