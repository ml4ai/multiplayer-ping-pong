import pygame
import config as cfg
from random import randint
from typing import Optional
from math import copysign


class Ball(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()

        self.image = pygame.Surface([cfg.BALL_SIZE, cfg.BALL_SIZE])
        self.image.fill((0, 0, 0))
        self.image.set_colorkey((0, 0, 0))

        pygame.draw.rect(self.image, cfg.FOREGROUND_COLOR, [0, 0, cfg.BALL_SIZE, cfg.BALL_SIZE])

        self.velocity = [cfg.BALL_X_SPEED, randint(-8, 8)]

        self.rect = self.image.get_rect()
        self.rect.x = 545
        self.rect.y = 395

    def update(self):
        self.rect.x += self.velocity[0]
        self.rect.y += self.velocity[1]

    def bounce(self, velocity_y: Optional[int] = None):
        if velocity_y is not None:
            assert isinstance(velocity_y, int)

        self.velocity[0] = -self.velocity[0]

        velocity_y_sign = copysign(1, self.velocity[1])
        self.velocity[1] = velocity_y if velocity_y is not None else velocity_y_sign * randint(2, 5)
