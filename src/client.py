import pygame
import sys
import threading
import socket
from select import select
import json
from utils import send
from utils import Paddle
from utils import Ball
import config as cfg

class Client:
    def __init__(self):
        host = sys.argv[1]
        port = int(sys.argv[2])

        self._team = sys.argv[3]

        self._client_id = -1

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

        # Set up game window
        screen = pygame.display.set_mode(cfg.WINDOW_SIZE)
        pygame.display.set_caption("Multiplayer Ping Pong")

        while self._running:
            # Exit the game if user hits close
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._running = False

                    # Notify server that client closes the connection
                    _, writable, _ = select([], [self._to_server], [self._to_server])
                    if writable:
                        send(writable[0], "CLOSE")
                    else:
                        raise RuntimeError("Lost connection with server")

            if not self._running:
                break

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

            # Add sprites to sprite group
            all_sprites_list = pygame.sprite.Group()
            for object_id, position in data["positions"].items():
                # The ball's position is at index 0
                if int(object_id) == 0:
                    ball = Ball()
                    ball.rect.x, ball.rect.y = position
                    all_sprites_list.add(ball)
                elif int(object_id) == self._client_id:
                    paddle = Paddle(position, 0, cfg.WINDOW_SIZE[1] - 100, cfg.PLAYER_COLOR)
                    all_sprites_list.add(paddle)
                else:
                    paddle = Paddle(position, 0, cfg.WINDOW_SIZE[1] - 100)
                    all_sprites_list.add(paddle)

            # Draw background
            screen.fill((0, 0, 0))

            # Draw sprite group
            all_sprites_list.draw(screen)

            #Display scores:
            font = pygame.font.Font(None, 74)
            text = font.render(str(data["score_left"]), 1, (255, 255, 255))
            screen.blit(text, (420,10))
            text = font.render(str(data["score_right"]), 1, (255, 255, 255))
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
        _, writable, _ = select([], [self._to_server], [self._to_server])
        if writable:
            send(writable[0], self._team)
        else:
            raise RuntimeError("Lost connection with server")

        clock = pygame.time.Clock() # Control the rate of sending data to server
        while self._running:
            # Get keys pressed by user
            keys = pygame.key.get_pressed()

            # Send control commands to server
            if keys[pygame.K_UP]:
                _, writable, _ = select([], [self._to_server], [self._to_server])
                if writable:
                    try:
                        send(writable[0], "UP")
                    except BrokenPipeError:
                        print("Server closed")
                        self._running = False

            elif keys[pygame.K_DOWN]:
                _, writable, _ = select([], [self._to_server], [self._to_server])
                if writable:
                    try:
                        send(writable[0], "DOWN")
                    except BrokenPipeError:
                        print("Server closed")
                        self._running = False
            
            # Limit loop rate to 120 loops per second
            clock.tick(120)
        
        # Close sending connection
        self._to_server.close()
        
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

    client = Client()
    client.run()
