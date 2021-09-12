import pygame

PADDLE_WIDTH = 10
PADDLE_HEIGHT = 100
PADDLE_COLOR = (255, 255, 255)

def draw_paddle(width: int, height: int, color: int):
    image = pygame.Surface((width, height))
    image.fill((0, 0 ,0))
    image.set_colorkey((0, 0 ,0))
    pygame.draw.rect(image, color, (0, 0, width, height))
    return image.get_rect()

class Paddle(pygame.sprite.Sprite):
    def __init__(self, x_position, upper_height: int, lower_height: int):
        super().__init__()
        self.paddle = draw_paddle(PADDLE_WIDTH, PADDLE_HEIGHT, PADDLE_COLOR)
        self.paddle.y = 0
        self.paddle.x = x_position

        self.speed = 5
        self.upper_height = upper_height
        self.lower_height = lower_height

    def move_up(self):
        self.paddle.y = max(self.upper_height, self.paddle.y - self.speed)
        return self.paddle.y

    def move_down(self):
        self.paddle.y = min(self.lower_height, self.paddle.y + self.speed)
        return self.paddle.y
