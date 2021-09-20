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

        # Establish two-channel connection to server
        self._from_server = Network.from_address(host, port)
        self._to_server = Network.from_address(host, port + 1)

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

        # Set up game window
        screen = pygame.display.set_mode(cfg.WINDOW_SIZE)
        pygame.display.set_caption("Multiplayer Ping Pong")

        while self._running:
            # Exit the game if user hits close
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._running = False

                    # Notify server that client closes the connection
                    self._to_server.send('x')

            if not self._running:
                break

            # Get update from server about the state of the game
            game_state = self._from_server.receive()

            # Exit game when server is closed
            if game_state["exit_request"]:
                self._running = False
                print("Server closed")
                break

            # Add sprites to sprite group
            all_sprites_list = pygame.sprite.Group()
            for object_id, position in game_state["positions"].items():
                # The ball's position is at index 0
                if int(object_id) == 0:
                    ball = Ball()
                    ball.rect.x, ball.rect.y = position
                    all_sprites_list.add(ball)
                # The paddles' positions start at index 1
                else:
                    paddle = Paddle(position, 0, cfg.WINDOW_SIZE[1] - 100)
                    all_sprites_list.add(paddle)

            # Draw background
            screen.fill((0, 0, 0))

            # Draw sprite group
            all_sprites_list.draw(screen)

            #Display scores:
            font = pygame.font.Font(None, 74)
            text = font.render(str(game_state["score_left"]), 1, (255, 255, 255))
            screen.blit(text, (420,10))
            text = font.render(str(game_state["score_right"]), 1, (255, 255, 255))
            screen.blit(text, (650,10))

            # Update client screen
            pygame.display.flip()
        
        # Close receiving connection
        self._from_server.close()

        # Close pygame window
        pygame.quit()

        # Wait for threads to finish
        control_thread.join()
        client_control_thread.join()

    def _send_input(self):
        """
        Send user's input command to server
        """
        # Notify server the team the client wants to be on
        self._to_server.send(self._team)

        clock = pygame.time.Clock() # Control the rate of sending data to server
        while self._running:
            # Get keys pressed by user
            keys = pygame.key.get_pressed()

            # Send control commands to server
            if keys[pygame.K_UP]:
                self._to_server.send("UP")
            elif keys[pygame.K_DOWN]:
                self._to_server.send("DOWN")
            
            # Limit loop rate to 120 loops per second
            clock.tick(120)
        
        # Close sending connection
        self._to_server.close()
        
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

    client = Client()
    client.run()
