from pgiud import *
from screens import Screen
from utility import *


class SettingsScreen:
    def initialize(self, app):
        self.from_game = False

    def load(self, app, from_game):
        self.from_game = from_game

    def update(self, app):
        hover = is_point_in_rect(
            app.mouse_pos,
            V(app.screen_right.x, app.screen_bottom.y),
            V(
                app.screen_right.x - (130 * app.scale),
                app.screen_bottom.y + (40 * app.scale),
            ),
        )
        if hover:
            if app.mouse_pressed:
                if self.from_game:
                    app.set_screen(Screen.PAUSED)
                else:
                    app.set_screen(Screen.MAIN_MENU)

    def draw(self, app):
        if self.from_game:
            if "--remove-transparency" not in app.argv:
                app.playing_screen.draw(app)
                app.fill_rect(
                    app.screen_bottom_left, app.screen_top_right, Color(0, 0, 0, 150)
                )
        app.draw_text(
            "No settings yet...",
            app.screen_center,
            app.main_font.new_size(int(22 * app.scale)),
            Color(220, 220, 220),
            Origin.CENTER,
        )
        hover = is_point_in_rect(
            app.mouse_pos,
            V(app.screen_right.x, app.screen_bottom.y),
            V(
                app.screen_right.x - (130 * app.scale),
                app.screen_bottom.y + (40 * app.scale),
            ),
        )
        app.fill_rounded_rect(
            V(app.screen_right.x, app.screen_bottom.y),
            V(
                app.screen_right.x - (130 * app.scale),
                app.screen_bottom.y + (40 * app.scale),
            ),
            Color(40, 40, 40) if hover else Color(30, 30, 30),
            int(1 * app.scale),
            Color(50, 50, 50),
            top_left_roundness=10 * app.scale,
            steps=10,
        )
        app.draw_text(
            "Back",
            V(
                app.screen_right.x - (65 * app.scale),
                app.screen_bottom.y + (20 * app.scale),
            ),
            app.main_font.new_size(int(30 * app.scale)),
            Color(255, 255, 255),
            Origin.CENTER,
        )
