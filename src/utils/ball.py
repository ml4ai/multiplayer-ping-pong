import pygame
import config as cfg
from random import randint
from typing import Optional
from math import copysign


class Ball(pygame.sprite.Sprite):
    """
    Ball pygame sprite updated by the server
    """
    def __init__(self,
                 ball_size: int,
                 ball_x_speed: int):
        # Set up pygame sprite
        super().__init__()
        self.image = pygame.Surface([ball_size, ball_size])
        self.image.fill((0, 0, 0))
        self.image.set_colorkey((0, 0, 0))
        pygame.draw.rect(self.image, cfg.FOREGROUND_COLOR, [0, 0, ball_size, ball_size])

        self._ball_size = ball_size
        self._ball_x_speed = ball_x_speed

        self.rect = self.image.get_rect()
        self.rect.x = int((cfg.WINDOW_SIZE[0] + ball_size) / 2)
        self.rect.y = int((cfg.WINDOW_SIZE[1] + ball_size) / 2)

        # Initialize ball velocity
        self.velocity = [ball_x_speed, randint(-ball_x_speed, ball_x_speed)]

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
            self.velocity[1] = velocity_y_sign * randint(4, self._ball_x_speed)
    
    def reset_center(self):
        self.rect.x = int((cfg.WINDOW_SIZE[0] + self._ball_size) / 2)
        self.rect.y = int((cfg.WINDOW_SIZE[1] + self._ball_size) / 2)

        # Re-initialize ball velocity
        self.velocity = [self._ball_x_speed, randint(-self._ball_x_speed, self._ball_x_speed)]
