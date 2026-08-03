"""
Bouncing Ball Simulator — pygame desktop version.

Physics lives in ball_physics.py so it can be shared with the
Kivy/Android version (main.py).

Controls:
    R            — reset the ball to the top
    SPACE        — pause / unpause
    + / -        — increase / decrease gravity
    ESC or QUIT  — exit
"""

import sys

import pygame

from ball_physics import (
    WIDTH, HEIGHT, GROUND_Y, BALL_RADIUS,
    GRAVITY, RESTITUTION, AIR_RESISTANCE,
    BG_COLOR, GROUND_COLOR, TEXT_COLOR,
    Ball,
)


# ---------------------------------------------------------------------------
# Helpers  (pygame-specific rendering)
# ---------------------------------------------------------------------------
def draw_ground(surface: pygame.Surface):
    pygame.draw.rect(surface, GROUND_COLOR,
                     (0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y))
    # a little texture line
    for i in range(0, WIDTH, 20):
        pygame.draw.line(surface, (60, 100, 60),
                         (i, GROUND_Y + 10), (i + 10, GROUND_Y + 10), 1)


def draw_hud(surface: pygame.Surface, ball: Ball, paused: bool, clock: pygame.time.Clock):
    font = pygame.font.SysFont("consolas", 18)
    lines = [
        f"gravity : {ball.gravity:.0f} px/s²  ('+' / '-' to change)",
        f"velocity: ({ball.vx:+.1f}, {ball.vy:+.1f}) px/s",
        f"height  : {GROUND_Y - ball.y:.1f} px",
        "SPACE = pause  |  R = reset  |  ESC = quit",
    ]
    if paused:
        lines.append("▶ PAUSED")
    for idx, line in enumerate(lines):
        img = font.render(line, True, TEXT_COLOR)
        surface.blit(img, (12, 12 + idx * 22))

    fps = clock.get_fps()
    if fps:
        img = font.render(f"{fps:.0f} FPS", True, TEXT_COLOR)
        surface.blit(img, (WIDTH - img.get_width() - 12, 12))


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Bouncing Ball Simulator  ·  code-puppy")
    clock = pygame.time.Clock()

    ball = Ball(WIDTH / 2, 80)
    paused = False

    running = True
    while running:
        dt = clock.tick(120) / 1000   # delta-time in seconds (capped at 120 FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                match event.key:
                    case pygame.K_ESCAPE:
                        running = False
                    case pygame.K_SPACE:
                        paused = not paused
                    case pygame.K_r:
                        ball.reset()
                        paused = False
                    case pygame.K_EQUALS | pygame.K_KP_PLUS:
                        ball.gravity += 50
                    case pygame.K_MINUS | pygame.K_KP_MINUS:
                        ball.gravity = max(50, ball.gravity - 50)

        if not paused:
            ball.step(dt)

        # --- draw ---
        screen.fill(BG_COLOR)
        draw_ground(screen)
        ball.draw(screen)
        draw_hud(screen, ball, paused, clock)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
