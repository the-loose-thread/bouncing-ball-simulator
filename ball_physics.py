"""
ball_physics.py — pure physics for the bouncing ball simulator.

No GUI dependencies.  Both bouncing_ball.py (pygame) and main.py (Kivy)
import from here so the physics lives in one place (DRY).
"""

from dataclasses import dataclass


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
WIDTH = 800
HEIGHT = 600
GROUND_Y = HEIGHT - 50           # y-coordinate of the ground line
BALL_RADIUS = 25
BALL_MASS = 1.0                  # kept for clarity / future expansion

GRAVITY = 900.0                  # pixels / s²
RESTITUTION = 0.96               # bounce energy retention (0 = no bounce, 1 = perfect)
AIR_RESISTANCE = 0.998           # tiny drag per frame so the ball settles

# Visual constants (shared so Kivy and pygame look the same)
BG_COLOR = (30, 30, 40)
GROUND_COLOR = (80, 120, 80)
BALL_COLOR = (240, 220, 60)
TEXT_COLOR = (220, 220, 220)


# ---------------------------------------------------------------------------
# Ball entity
# ---------------------------------------------------------------------------
@dataclass
class Ball:
    """A simple point-mass ball with position and velocity."""
    x: float
    y: float
    vx: float = 0.0
    vy: float = 0.0
    radius: int = BALL_RADIUS
    mass: float = BALL_MASS
    gravity: float = GRAVITY
    restitution: float = RESTITUTION

    def reset(self, x=None, y=None):
        """Drop the ball from rest at *x*, *y* (defaults to spawn point)."""
        self.x = x if x is not None else WIDTH / 2
        self.y = y if y is not None else 80
        self.vx = 0.0
        self.vy = 0.0

    def step(self, dt: float):
        """Advance physics by *dt* seconds."""
        # Apply gravity (acceleration)
        self.vy += self.gravity * dt

        # Apply gentle air resistance
        self.vx *= AIR_RESISTANCE
        self.vy *= AIR_RESISTANCE

        # Integrate position (semi-implicit / symplectic Euler)
        self.x += self.vx * dt
        self.y += self.vy * dt

        # Floor collision
        if self.y + self.radius > GROUND_Y:
            self.y = GROUND_Y - self.radius
            # Invert vertical velocity, scaled by restitution
            self.vy = -self.vy * self.restitution
            self.vx *= self.restitution
            # Stop tiny jitter when the ball has effectively come to rest
            if abs(self.vy) < 30:
                self.vy = 0.0

        # Wall collisions (left / right)
        if self.x - self.radius < 0:
            self.x = self.radius
            self.vx = -self.vx * self.restitution
        elif self.x + self.radius > WIDTH:
            self.x = WIDTH - self.radius
            self.vx = -self.vx * self.restitution

    def draw(self, surface):
        """Draw on a pygame Surface (kept for backwards compat)."""
        import pygame
        pygame.draw.circle(surface, BALL_COLOR,
                           (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surface, (230, 200, 40),
                           (int(self.x), int(self.y)), self.radius, width=2)
