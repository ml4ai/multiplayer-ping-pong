import sys
import threading
import pygame
import config as cfg
from utils import Network


class AIClient:
    def __init__(self):
        host = sys.argv[1]
        port = int(sys.argv[2])

        self._team = sys.argv[3]

        # Establish two-channel connection to server
        self._from_server = Network.from_address(host, port)
        self._to_server = Network.from_address(host, port + 1)

        # Monitor paddle's and ball's position
        self._ball_position = [0, 0]
        self._paddle_position = [0, 0]

        self._paddle_id = -1 # store paddle id

        self._running = True

    def run(self):
        """
        Run ping pong on client's side
        """
        # Create a thread for sending client input to server
        control_thread = threading.Thread(target=self._send_input)
        control_thread.start()
        
        # Create a thread to control client through terminal
        client_control_thread = threading.Thread(target=self._client_control)
        client_control_thread.start()

        while self._running:
            game_state = self._from_server.receive()

            # Exit game when server is closed
            if game_state["exit_request"]:
                self._running = False
                print("Server closed")
                break

            for object_id, position in game_state["positions"].items():
                # Get ball position (located at index 0)
                if int(object_id) == 0:
                    self._ball_position = position
                # Get AI's paddle's location
                elif int(object_id) == self._paddle_id:
                    self._paddle_position = position

        control_thread.join()
        client_control_thread.join()

    def _send_input(self):
        """
        Send AI's input command to server
        """
        # Notify server the team the client wants to be on
        self._to_server.send(self._team)

        # Wait for server to indicate the AI's paddle's id
        self._paddle_id = int(self._to_server.receive())

        clock = pygame.time.Clock() # Control the rate of sending data to server
        while self._running:
            # Send control commands to server
            # Note that positions specify the location of the top left corners of the sprites

            # Go up when the ball is above the paddle
            if (self._ball_position[1] + cfg.BALL_SIZE / 2.0) - (self._paddle_position[1] + cfg.PADDLE_HEIGHT / 2.0) < 10:
                self._to_server.send("UP")
            # Go down when the ball is below the paddle
            elif (self._ball_position[1] + cfg.BALL_SIZE / 2.0) - (self._paddle_position[1] + cfg.PADDLE_HEIGHT / 2.0) > 10:
                self._to_server.send("DOWN")
            
            # Limit loop rate to 120 loops per second
            clock.tick(120)

    def _client_control(self):
        """
        Control client
        """
        while self._running:
            command = input()
            
            if command == "exit":
                self._running = False
                self._to_server.send('x')
            else:
                print("Unknown command")


if __name__ == "__main__":
    pygame.init()

    ai_client = AIClient()
    ai_client.run()
