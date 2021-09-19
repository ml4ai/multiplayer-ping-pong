import pygame
import config as cfg
from random import randint
from typing import Optional
from math import copysign

CENTER_X = int((cfg.WINDOW_SIZE[0] + cfg.BALL_SIZE) / 2)
CENTER_Y = int((cfg.WINDOW_SIZE[1] + cfg.BALL_SIZE) / 2)


class Ball(pygame.sprite.Sprite):
    """
    Ball pygame sprite updated by the server
    """
    def __init__(self):
        # Set up pygame sprite
        super().__init__()
        self.image = pygame.Surface([cfg.BALL_SIZE, cfg.BALL_SIZE])
        self.image.fill((0, 0, 0))
        self.image.set_colorkey((0, 0, 0))
        pygame.draw.rect(self.image, cfg.FOREGROUND_COLOR, [0, 0, cfg.BALL_SIZE, cfg.BALL_SIZE])

        self.rect = self.image.get_rect()
        self.rect.x = CENTER_X
        self.rect.y = CENTER_Y

        # Initialize ball velocity
        self.velocity = [cfg.BALL_X_SPEED, randint(-5, 5)]

    def update(self):
        """
        Update position of the ball
        """
        self.rect.x += int(self.velocity[0])
        self.rect.y += int(self.velocity[1])

    def bounce(self, velocity_y: Optional[int] = None):
        """
        Bounce the ball when it hits players' wall or paddle
        """
        # Move the ball the other direction
        self.velocity[0] = -self.velocity[0]

        # If the y velocity is set by user
        if velocity_y is not None:
            assert isinstance(velocity_y, int)
            self.velocity[1] = velocity_y

        # Randomly generate y velocity, following its previous trajectory
        else:
            velocity_y_sign = copysign(1, self.velocity[1])
            self.velocity[1] = velocity_y_sign * randint(2, 5)
    
    def reset_center(self):
        self.rect.x = CENTER_X
        self.rect.y = CENTER_Y

        # Re-initialize ball velocity
        self.velocity = [cfg.BALL_X_SPEED, randint(-5, 5)]
