"""
main.py — Kivy bouncing ball simulator  (Android-ready entry point).

Physics is shared with bouncing_ball.py via ball_physics.py.
Touch controls for mobile, keyboard controls for desktop.

Touch / Click:
    Tap          — reset ball to top
    Double tap   — pause / unpause
"""

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle, Ellipse, Line
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.utils import platform

from car_notification import create_car_notification, get_notification_status
from ball_physics import (
    WIDTH, HEIGHT, GROUND_Y, BALL_RADIUS,
    GRAVITY, BG_COLOR, GROUND_COLOR,
    Ball,
)


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------
def rgba(rgb):
    """Convert a 0–255 RGB tuple to a 0-1 Kivy rgba list."""
    return [c / 255 for c in rgb] + [1]


# ------------------------------------------------------------------
# Game canvas
# ------------------------------------------------------------------
class BallWorld(Widget):
    """Draws and steps the Ball, scaling the 800×600 physics to any screen."""

    def __init__(self, **kwargs):
        # Init state before super().__init__ so on_size callbacks are safe.
        self.ball = Ball(WIDTH / 2, 80)
        self.paused = False
        self._hud_labels = {}
        self._scale = 1.0
        self._ox = 0.0
        self._oy = 0.0
        super().__init__(**kwargs)
        self.bind(size=self._layout, pos=self._layout)

    # -- coordinate mapping ----------------------------------------------
    def _phys_to_screen(self, px, py):
        """Physics (x, y-down) → screen (x, y-up), scaled + centered."""
        sx = self._ox + px * self._scale
        sy = self._oy + (HEIGHT - py) * self._scale
        return sx, sy

    # -- layout / redraw -------------------------------------------------
    def _layout(self, *_):
        w, h = self.size
        self._scale = min(w / WIDTH, h / HEIGHT)
        self._ox = (w - WIDTH * self._scale) / 2
        self._oy = (h - HEIGHT * self._scale) / 2
        self._redraw_all()

    def _redraw_all(self, *_):
        """Full redraw of background + ground + ball."""
        self.canvas.before.clear()
        self.canvas.clear()

        with self.canvas.before:
            Color(*rgba(BG_COLOR))
            Rectangle(pos=self.pos, size=self.size)

            Color(*rgba(GROUND_COLOR))
            gx, gy = self._phys_to_screen(0, GROUND_Y)
            gw = WIDTH * self._scale
            gh = (HEIGHT - GROUND_Y) * self._scale
            Rectangle(pos=(gx, gy - gh), size=(gw, gh))

            Color(*rgba((60, 100, 60)))
            for i in range(0, int(gw), 20):
                Line(points=(gx + i, gy - gh, gx + i + 10, gy - gh), width=1)

        with self.canvas:
            self._draw_ball_gfx()

    def _draw_ball_gfx(self):
        r = BALL_RADIUS * self._scale
        sx, sy = self._phys_to_screen(self.ball.x, self.ball.y)
        Color(*rgba((245, 225, 60)))
        Ellipse(pos=(sx - r, sy - r), size=(r * 2, r * 2))
        Color(*rgba((230, 200, 40)))
        Ellipse(pos=(sx - r, sy - r), size=(r * 2, r * 2))

    def _redraw_ball(self):
        """Clear and redraw just the ball (called each physics tick)."""
        self.canvas.clear()
        with self.canvas:
            self._draw_ball_gfx()

    # -- HUD -------------------------------------------------------------
    def set_hud(self, labels):
        self._hud_labels = labels
        self._update_hud()

    def _update_hud(self, *_):
        if not self._hud_labels:
            return
        for key, lbl in self._hud_labels.items():
            if key == 'gravity':
                lbl.text = f"gravity: {self.ball.gravity:.0f}"
            elif key == 'velocity':
                lbl.text = f"velocity: ({self.ball.vx:+.1f}, {self.ball.vy:+.1f})"
            elif key == 'height':
                lbl.text = f"height: {GROUND_Y - self.ball.y:.1f}"
            elif key == 'status':
                lbl.text = "⏸ PAUSED" if self.paused else ""

            elif key == 'notif':
                lbl.text = f"notif: {get_notification_status()[:40]}"

    # -- game loop -------------------------------------------------------
    def start(self):
        Clock.schedule_interval(self._tick, 1 / 120)

    def _tick(self, dt):
        if not self.paused:
            self.ball.step(dt)
            self._redraw_ball()
        self._update_hud()

    # -- input -----------------------------------------------------------
    def on_touch_down(self, touch):
        if touch.is_double_tap:
            self.paused = not self.paused
        else:
            self.ball.reset()
            self.paused = False
        self._update_hud()
        super().on_touch_down(touch)


# ------------------------------------------------------------------
# Controls
# ------------------------------------------------------------------
class Controls(FloatLayout):
    """On-screen buttons for mobile friendliness."""

    def __init__(self, world: BallWorld, **kwargs):
        super().__init__(**kwargs)
        self.world = world
        self._build()

    def _build(self):
        btn_w, btn_h = dp(90), dp(55)
        gap = dp(10)
        start_x = (Window.width - (4 * btn_w + 3 * gap)) / 2
        bottom = dp(15)

        for i, (label, cb) in enumerate([
            ("RESET", lambda *_: self.world.ball.reset()),
            ("PAUSE", lambda *_: setattr(self.world, "paused",
                                         not self.world.paused)),
            ("+GRAV",  lambda *_: setattr(self.world.ball, "gravity",
                                          self.world.ball.gravity + 50)),
            ("-GRAV",  lambda *_: setattr(self.world.ball, "gravity",
                                          max(50, self.world.ball.gravity - 50))),
        ]):
            btn = Button(text=label, font_size=sp(14),
                         size_hint=(None, None),
                         size=(btn_w, btn_h),
                         pos=(start_x + i * (btn_w + gap), bottom))
            btn.bind(on_release=cb)
            self.add_widget(btn)


# ------------------------------------------------------------------
# App
# ------------------------------------------------------------------
class BouncingBallApp(App):
    def build(self):
        if platform != 'android':
            Window.size = (WIDTH, HEIGHT)
        Window.clear()

        # Android Auto: create a persistent notification so the user can
        # tap it from the car screen to launch the bouncing ball.
        create_car_notification()

        root = FloatLayout()

        world = BallWorld()
        root.add_widget(world)

        # HUD labels
        hud = {}
        for i, (key, init) in enumerate([
            ('gravity', f"gravity: {GRAVITY:.0f}"),
            ('velocity', "velocity: 0.0, 0.0"),
            ('height',   "height: 0.0"),
            ('status',   ""),
            ('version',  "v1.4 - AA Debug"),
            ('notif',  "notif: ..."),
        ]):
            lbl = Label(text=init, color=rgba((220, 220, 220)),
                        font_size=sp(14), halign='left',
                        valign='middle',
                        size_hint=(None, None),
                        size=(dp(260), dp(26)),
                        pos=(dp(12), Window.height - dp(44) - i * dp(28)))
            hud[key] = lbl
            root.add_widget(lbl)
        world.set_hud(hud)

        # Controls
        root.add_widget(Controls(world))

        # Start physics after first layout pass
        Clock.schedule_once(lambda dt: world.start(), 0.1)

        return root


if __name__ == '__main__':
    BouncingBallApp().run()
