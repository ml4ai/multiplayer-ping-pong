import pygame
import config as cfg


class Paddle(pygame.sprite.Sprite):
    """
    Paddle pygame sprite controlled by the client.
    """
    def __init__(self, position, upper_height: int, lower_height: int):
        # Set up pygame sprite
        super().__init__()
        self.image = pygame.Surface((cfg.PADDLE_WIDTH, cfg.PADDLE_HEIGHT))
        self.image.fill((0, 0 ,0))
        self.image.set_colorkey((0, 0 ,0))
        pygame.draw.rect(self.image, cfg.FOREGROUND_COLOR, (0, 0, cfg.PADDLE_WIDTH, cfg.PADDLE_HEIGHT))

        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = position

        # Store game information
        self._speed = cfg.PADDLE_SPEED
        self._upper_height = upper_height
        self._lower_height = lower_height

    def move_up(self):
        """
        Move paddle up
        """
        # Ensure that paddle does not move above the screen.
        self.rect.y = max(self._upper_height, self.rect.y - self._speed)
        return self.rect.y

    def move_down(self):
        """
        Move paddle down
        """
        # Ensure that paddle does not move below the screen.
        self.rect.y = min(self._lower_height, self.rect.y + self._speed)
        return self.rect.y
