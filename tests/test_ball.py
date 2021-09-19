import pytest
from utils import Ball
import config as cfg

PADDLE_POSITION = (0, 0)
PADDLE_Y_UPPER_HEIGHT = 0

@pytest.fixture()
def ball():
    return Ball()

def test_constructor(ball):
    assert ball.rect.x == int((cfg.WINDOW_SIZE[0] + cfg.BALL_SIZE) / 2)
    assert ball.rect.y == int((cfg.WINDOW_SIZE[1] + cfg.BALL_SIZE) / 2)

def test_update(ball):
    current_position_x = ball.rect.x
    current_position_y = ball.rect.y

    ball.update()

    assert ball.rect.x == current_position_x + ball.velocity[0]
    assert ball.rect.y == current_position_y + ball.velocity[1]

def test_bounce_random(ball):
    ball.velocity[1] = 100
    current_velocity_x, current_velocity_y = ball.velocity

    ball.bounce()

    assert ball.velocity[0] == -current_velocity_x
    assert ball.velocity[1] != current_velocity_y

def test_bounce_set_y_velocity(ball):
    current_velocity_x = ball.velocity[0]

    y_new_velocity = 4
    ball.bounce(y_new_velocity)

    assert ball.velocity[0] == -current_velocity_x
    assert ball.velocity[1] == y_new_velocity

def test_bounce_set_invalid_y_type(ball):
    with pytest.raises(AssertionError):
        ball.bounce(4.0)
