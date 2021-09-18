import pygame
import sys
import threading
from utils import Paddle
from utils import Ball
from utils import Network
import config as cfg

class Client:
    def __init__(self):
        host = sys.argv[1]
        port = int(sys.argv[2])

        self._team = sys.argv[3]

        self._from_server = Network.from_address(host, port)
        self._to_server = Network.from_address(host, port + 1)

        self._running = True

    def run(self):
        control_thread = threading.Thread(target=self._send_input)
        control_thread.start()

        # Set up game window
        screen = pygame.display.set_mode(cfg.WINDOW_SIZE)
        pygame.display.set_caption("Multiplayer Ping Pong")

        while self._running:
            # Exit the game if user hits close
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._running = False
            if not self._running:
                break

            data = self._from_server.receive()

            all_sprites_list = pygame.sprite.Group()
            for object_id, position in data["positions"].items():
                if int(object_id) == 0:
                    ball = Ball()
                    ball.rect.x = position[0]
                    ball.rect.y = position[1]
                    all_sprites_list.add(ball)
                else:
                    paddle = Paddle(position[0], 0, cfg.WINDOW_SIZE[1] - 100)
                    paddle.rect.y = position[1]
                    all_sprites_list.add(paddle)

            # Draw background
            screen.fill((0, 0, 0))

            all_sprites_list.draw(screen)

            #Display scores:
            font = pygame.font.Font(None, 74)
            text = font.render(str(data["score_left"]), 1, (255, 255, 255))
            screen.blit(text, (420,10))
            text = font.render(str(data["score_right"]), 1, (255, 255, 255))
            screen.blit(text, (650,10))

            # Update screen
            pygame.display.flip()

        self._to_server.send('x')
        self._from_server.close()
        pygame.quit()

        control_thread.join()

    def _send_input(self):
        self._to_server.send(self._team)

        clock = pygame.time.Clock()
        while self._running:
            keys = pygame.key.get_pressed()

            # Send control commands to server
            if keys[pygame.K_UP]:
                self._to_server.send("UP")
            elif keys[pygame.K_DOWN]:
                self._to_server.send("DOWN")
            
            clock.tick(120)
        
        self._to_server.close()


if __name__ == "__main__":
    pygame.init()

    client = Client()
    client.run()
