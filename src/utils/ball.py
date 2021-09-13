import pygame
from random import randint

BALL_SIZE = 10
WHITE = (255, 255, 255)
BALL_SPEED = 8

class Ball(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()

        self.image = pygame.Surface([BALL_SIZE, BALL_SIZE])
        self.image.fill((0, 0, 0))
        self.image.set_colorkey((0, 0, 0))

        pygame.draw.rect(self.image, WHITE, [0, 0, BALL_SIZE, BALL_SIZE])

        self.velocity = [BALL_SPEED, randint(-8, 8)]

        self.rect = self.image.get_rect()
        self.rect.x = 545
        self.rect.y = 395

    def update(self):
        self.rect.x += self.velocity[0]
        self.rect.y += self.velocity[1]

    def bounce(self):
        self.velocity[0] = -self.velocity[0]
        self.velocity[1] = randint(-8, 8)
