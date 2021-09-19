import pytest
from utils import Paddle
import config as cfg

PADDLE_POSITION = (0, 0)
PADDLE_Y_UPPER_HEIGHT = 0

@pytest.fixture()
def paddle():
    return Paddle(PADDLE_POSITION, PADDLE_Y_UPPER_HEIGHT, cfg.WINDOW_SIZE[1] - cfg.PADDLE_HEIGHT)

def test_constructor(paddle):
    assert (paddle.rect.x, paddle.rect.y) == PADDLE_POSITION

def test_move_up_at_top(paddle):
    paddle.rect.y = paddle._upper_height
    assert paddle.move_up() == paddle._upper_height

def test_move_up(paddle):
    original_y = 200
    paddle.rect.y = original_y
    assert paddle.move_up() < original_y

def test_move_down_at_bottom(paddle):
    paddle.rect.y = paddle._lower_height
    assert paddle.move_down() == paddle._lower_height

def test_move_down(paddle):
    original_y = 200
    paddle.rect.y = original_y
    assert paddle.move_down() > original_y