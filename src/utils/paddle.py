import pygame

PADDLE_WIDTH = 10
PADDLE_HEIGHT = 100
PADDLE_COLOR = (255, 255, 255)


class Paddle(pygame.sprite.Sprite):
    def __init__(self, x_position, upper_height: int, lower_height: int):
        super().__init__()
        self.image = pygame.Surface((PADDLE_WIDTH, PADDLE_HEIGHT))
        self.image.fill((0, 0 ,0))
        self.image.set_colorkey((0, 0 ,0))
        pygame.draw.rect(self.image, PADDLE_COLOR, (0, 0, PADDLE_WIDTH, PADDLE_HEIGHT))

        self.rect = self.image.get_rect()
        self.rect.y = 0
        self.rect.x = x_position

        self.speed = 10
        self.upper_height = upper_height
        self.lower_height = lower_height

    def move_up(self):
        self.rect.y = max(self.upper_height, self.rect.y - self.speed)
        return self.rect.y

    def move_down(self):
        self.rect.y = min(self.lower_height, self.rect.y + self.speed)
        return self.rect.y
