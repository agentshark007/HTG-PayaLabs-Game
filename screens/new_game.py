from elements.selection_list import SelectionList
from pgiud import *
from screens import Screen
from utility import *


class NewGameScreen:
    def initialize(self, app):
        self.selection_list = SelectionList()
        self.selection_list.initialize(
            app, "Select Your God", app.gods, lambda god: god.name, "No gods found"
        )

    def load(self, app, args):
        pass

    def update(self, app):
        self.selection_list.update(app)
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
                app.set_screen(Screen.PLAYING)

    def _draw_god_details(self, app):
        god = app.gods[self.selection_list.selected_index]
        app.fill_rect(
            V(app.screen_right.x, app.screen_top.y),
            V(
                app.screen_right.x - (130 * app.scale),
                app.screen_top.y - (150 * app.scale),
            ),
            Color(30, 30, 30),
            int(2 * app.scale),
            Color(50, 50, 50),
        )
        app.fill_rect(
            V(app.screen_left.x + (150 * app.scale), app.screen_top.y),
            V(
                app.screen_right.x - (130 * app.scale),
                app.screen_top.y - (150 * app.scale),
            ),
            Color(0, 0, 0),
        )
        app.fill_rect(
            V(
                app.screen_left.x + (150 * app.scale),
                app.screen_top.y - (150 * app.scale),
            ),
            V(app.screen_right.x, app.screen_bottom.y),
            Color(0, 0, 0),
        )
        try:
            app.draw_image(
                app.god_images[god.image],
                V(
                    app.screen_right.x - (65 * app.scale),
                    app.screen_top.y - (75 * app.scale),
                ),
                origin=Origin.CENTER,
                scale_x=app.scale
                * 1.5
                * (math.sin(app.seconds_since_start * 2) * 0.1 + 0.9),
                scale_y=app.scale * 1.5,
                antialiasing=True,
            )
        except Exception:
            pass
        app.draw_text(
            god.name,
            V(
                app.screen_left.x + (155 * app.scale) + (3 * app.scale),
                app.screen_top.y,
            ),
            app.heading_font.new_size(int(25 * app.scale)),
            Color(255, 255, 255),
            Origin.TOP_LEFT,
        )
        app.draw_text_word_wrap(
            god.info,
            V(
                app.screen_left.x + (155 * app.scale) + (3 * app.scale),
                app.screen_top.y - (155 * app.scale) + (3 * app.scale),
            ),
            app.main_font.new_size(int(30 * app.scale)),
            Color(255, 255, 255),
            Origin.TOP_LEFT,
            wrap_distance=abs(
                app.screen_left.x
                - (app.screen_left.x + (155 * app.scale) + (3 * app.scale))
            )
            * 2,
        )

    def draw(self, app):
        self.selection_list.draw(app)
        if self.selection_list.selected_index != -1:
            self._draw_god_details(app)
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
            "Start Game",
            V(
                app.screen_right.x - (65 * app.scale),
                app.screen_bottom.y + (20 * app.scale),
            ),
            app.main_font.new_size(int(30 * app.scale)),
            Color(255, 255, 255),
            Origin.CENTER,
        )
