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

        self._from_server = Network.from_address(host, port)
        self._to_server = Network.from_address(host, port + 1)

        self._ball_position = [0, 0]
        self._paddle_position = [0, 0]

        self._paddle_id = -1

    def run(self):
        control_thread = threading.Thread(target=self._send_input)
        control_thread.start()

        while True:
            data = self._from_server.receive()
            for object_id, position in data["positions"].items():
                if int(object_id) == 0:
                    self._ball_position = position
                elif int(object_id) == self._paddle_id:
                    self._paddle_position = position

    def _send_input(self):
        self._to_server.send(self._team)
        self._paddle_id = int(self._to_server.receive())

        clock = pygame.time.Clock()
        while True:
            # Send control commands to server
            if (self._ball_position[1] + cfg.BALL_SIZE / 2.0) - (self._paddle_position[1] + cfg.PADDLE_HEIGHT / 2.0) < 10:
                self._to_server.send("UP")
            elif (self._ball_position[1] + cfg.BALL_SIZE / 2.0) - (self._paddle_position[1] + cfg.PADDLE_HEIGHT / 2.0) > 10:
                self._to_server.send("DOWN")
            
            clock.tick(120)


if __name__ == "__main__":
    pygame.init()

    ai_client = AIClient()
    ai_client.run()
