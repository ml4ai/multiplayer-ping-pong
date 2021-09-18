import pygame
import config as cfg


class Paddle(pygame.sprite.Sprite):
    def __init__(self, x_position, upper_height: int, lower_height: int):
        super().__init__()
        self.image = pygame.Surface((cfg.PADDLE_WIDTH, cfg.PADDLE_HEIGHT))
        self.image.fill((0, 0 ,0))
        self.image.set_colorkey((0, 0 ,0))
        pygame.draw.rect(self.image, cfg.FOREGROUND_COLOR, (0, 0, cfg.PADDLE_WIDTH, cfg.PADDLE_HEIGHT))

        self.rect = self.image.get_rect()
        self.rect.y = 0
        self.rect.x = x_position

        self._speed = cfg.PADDLE_SPEED
        self._upper_height = upper_height
        self._lower_height = lower_height

    def move_up(self):
        self.rect.y = max(self._upper_height, self.rect.y - self._speed)
        return self.rect.y

    def move_down(self):
        self.rect.y = min(self._lower_height, self.rect.y + self._speed)
        return self.rect.y
