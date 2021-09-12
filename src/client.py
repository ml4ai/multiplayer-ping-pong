import pygame
import sys
from utils import ClientNetwork

WINDOW_SIZE = (1100, 800)

if __name__ == "__main__":
    pygame.init()

    host = sys.argv[1]
    port = int(sys.argv[2])
    server_network = ClientNetwork.from_address(host, port)
    print(server_network.receive())

    # Set up game window
    screen = pygame.display.set_mode(WINDOW_SIZE)
    pygame.display.set_caption("Multiplayer Ping Pong")

    # Use clock to control framerate
    clock = pygame.time.Clock()

    running = True
    while running:
        # Exit the game if user hits close
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        if not running:
            break

        # Send control commands to server
        keys = pygame.key.get_pressed()

        # TODO: send control commands to server
        if keys[pygame.K_UP]:
            print("UP pressed")
        elif keys[pygame.K_DOWN]:
            print("DOWN pressed")
        
        # Draw background
        screen.fill((0, 0, 0))

        # Update screen
        pygame.display.flip()

        # Limit to 60 frames per second
        clock.tick(60)

    pygame.quit()