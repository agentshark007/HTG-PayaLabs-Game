from pgiud import *
from screens import Screen
from utility import *


class CreditsScreen:
    def initialize(self, app):
        pass

    def load(self, app, args):
        pass

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
                app.set_screen(Screen.MAIN_MENU)

    def draw(self, app):
        app.draw_text(
            "Credits",
            V(app.screen_top.x, app.screen_top.y - (20 * app.scale)),
            app.main_font.new_size(int(30 * app.scale)),
            Color(255, 255, 255),
            Origin.CENTER,
        )
        app.draw_text(
            "Fate of the Gods\nLead Developer: Andru Cupala\nGame Designer and God Creator: Aislinn Haist\nArtist: Danielle Miless\n\nandrucupala.com/payalabs\n\nCreated with python using pygame and pgiud",
            V(app.screen_top.x, app.screen_top.y - (40 * app.scale)),
            app.main_font.new_size(int(22 * app.scale)),
            Color(255, 255, 255),
            Origin.TOP,
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
