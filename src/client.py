import pygame
import sys
import threading
from utils import Network

WINDOW_SIZE = (1100, 800)

class Client:
    def __init__(self):
        host = sys.argv[1]
        port = int(sys.argv[2])
        self.server_network = Network.from_address(host, port)
        self.player_id = self.server_network.receive()
        self.running = True

    def run(self):
        control_thread = threading.Thread(target=self._send_input)
        control_thread.start()

        # Set up game window
        screen = pygame.display.set_mode(WINDOW_SIZE)
        pygame.display.set_caption("Multiplayer Ping Pong")

        # Use clock to control framerate
        clock = pygame.time.Clock()

        while self.running:
            # Exit the game if user hits close
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
            if not self.running:
                break

            print(self.server_network.receive())

            # Draw background
            screen.fill((0, 0, 0))

            # Update screen
            pygame.display.flip()

            # Limit to 60 frames per second
            clock.tick(60)

        self.server_network.send('x')
        pygame.quit()


    def _send_input(self):
        clock = pygame.time.Clock()
        while self.running:
            keys = pygame.key.get_pressed()

            # Send control commands to server
            if keys[pygame.K_UP]:
                self.server_network.send("UP")
            elif keys[pygame.K_DOWN]:
                self.server_network.send("DOWN")
            
            clock.tick(100)


if __name__ == "__main__":
    pygame.init()

    client = Client()
    client.run()
