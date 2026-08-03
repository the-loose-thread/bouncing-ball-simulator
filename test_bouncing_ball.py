"""
Test suite for bouncing_ball.py physics.

These tests verify the pure-physics logic of the Ball class — gravity,
bounces, walls, restitution, and reset.  They don't need a display.

Run with:  pytest test_bouncing_ball.py -v
"""

import math

import pytest

from ball_physics import (
    Ball,
    GROUND_Y,
    WIDTH,
    HEIGHT,
    BALL_RADIUS,
    GRAVITY,
    RESTITUTION,
    AIR_RESISTANCE,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def fresh_ball():
    """A ball dropped from rest at the default spawn point."""
    b = Ball(WIDTH / 2, 80)
    return b


@pytest.fixture
def ball_near_ground():
    """A ball resting just above the ground, ready to be dropped."""
    return Ball(WIDTH / 2, GROUND_Y - BALL_RADIUS)


# ---------------------------------------------------------------------------
# Gravity
# ---------------------------------------------------------------------------
class TestGravity:
    def test_accelerates_downward(self, fresh_ball):
        """Gravity should make vy positive (downward) after a step."""
        fresh_ball.step(0.01)
        assert fresh_ball.vy > 0

    def test_exact_gravity_increment(self, fresh_ball):
        """vy should increase by gravity * dt (before air resistance)."""
        vy_before = fresh_ball.vy
        fresh_ball.step(0.01)
        # gravity*dt = 900*0.01 = 9; after 0.998 air resistance ≈ 8.982
        expected_dvy = GRAVITY * 0.01 * AIR_RESISTANCE
        assert math.isclose(fresh_ball.vy - vy_before, expected_dvy, rel_tol=1e-6)


# ---------------------------------------------------------------------------
# Restitution / Bouncing
# ---------------------------------------------------------------------------
class TestBounce:
    def test_velocity_reverses_on_bounce(self, ball_near_ground):
        """When the ball hits the ground, vy should flip to upward (negative)."""
        ball_near_ground.vy = 200  # moving down hard
        ball_near_ground.step(0.05)
        assert ball_near_ground.vy < 0, "vy should reverse after hitting the ground"

    def test_restitution_scales_velocity(self, ball_near_ground):
        """Rebound velocity magnitude should be ~ restitution * impact velocity."""
        impact_vy = 300
        ball_near_ground.vy = impact_vy
        ball_near_ground.step(0.05)
        # After gravity + air-resistance, impact is slightly higher than 300;
        # the rebound is restitution * that.  Check order-of-magnitude.
        assert abs(ball_near_ground.vy) < impact_vy * RESTITUTION + 100

    def test_stops_jittering_at_rest(self):
        """Once vy is below the threshold, the ball should come to rest."""
        b = Ball(WIDTH / 2, GROUND_Y - BALL_RADIUS - 1)
        b.vy = 0.0
        # Simulate many frames; ball should settle on the ground
        for _ in range(500):
            b.step(0.016)  # ~60 FPS
        assert b.y == pytest.approx(GROUND_Y - BALL_RADIUS, abs=1)
        assert abs(b.vy) == pytest.approx(0, abs=1)


# ---------------------------------------------------------------------------
# Walls
# ---------------------------------------------------------------------------
class TestWalls:
    def test_left_wall_bounce(self):
        """Ball hitting the left wall should reverse vx."""
        b = Ball(BALL_RADIUS + 1, 200)
        b.vx = -150
        b.step(0.01)
        assert b.vx > 0, "vx should reverse off the left wall"
        assert b.x >= BALL_RADIUS

    def test_right_wall_bounce(self):
        """Ball hitting the right wall should reverse vx."""
        b = Ball(WIDTH - BALL_RADIUS - 1, 200)
        b.vx = 150
        b.step(0.01)
        assert b.vx < 0, "vx should reverse off the right wall"
        assert b.x <= WIDTH - BALL_RADIUS


# ---------------------------------------------------------------------------
# Reset
# ---------------------------------------------------------------------------
class TestReset:
    def test_reset_clears_velocity(self, fresh_ball):
        fresh_ball.vx = 100
        fresh_ball.vy = 500
        fresh_ball.reset()
        assert fresh_ball.vx == 0
        assert fresh_ball.vy == 0

    def test_reset_sets_spawn_position(self, fresh_ball):
        fresh_ball.x = 10
        fresh_ball.y = 500
        fresh_ball.reset()
        assert fresh_ball.x == WIDTH / 2
        assert fresh_ball.y == 80

    def test_reset_with_custom_position(self, fresh_ball):
        fresh_ball.vy = 999
        fresh_ball.reset(x=100, y=200)
        assert fresh_ball.x == 100
        assert fresh_ball.y == 200
        assert fresh_ball.vx == 0
        assert fresh_ball.vy == 0


# ---------------------------------------------------------------------------
# Energy loss over multiple bounces
# ---------------------------------------------------------------------------
class TestEnergyDissipation:
    def test_successive_bounces_get_smaller(self):
        """Each bounce peak height should be lower than the previous."""
        b = Ball(WIDTH / 2, 100)
        b.vy = 0
        peak_heights = []
        last_vy = 0
        for _ in range(3000):
            b.step(0.016)
            # track peak: when vy transitions from negative to positive
            if last_vy < 0 and b.vy >= 0:
                peak_heights.append(b.y)
            last_vy = b.vy
        # We should have at least 2 bounce peaks
        assert len(peak_heights) >= 2
        # Each peak (y value) should be increasing — ball bounces lower each time
        # (y increases downward, so a *higher* bounce means a *smaller* y)
        # Verify the ball is dissipating: later peaks should have larger y
        # (i.e., lower height).
        assert peak_heights[-1] > peak_heights[0], \
            "Ball should settle lower over successive bounces"
