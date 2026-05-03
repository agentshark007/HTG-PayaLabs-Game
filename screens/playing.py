from game import *
from pgiud import *
from screens import Screen
from utility import *


class PlayingScreen:
    def initialize(self, app):
        self.pause_button_size = 10
        self.pause_button_padding = 10
        self.pause_bars_size_x = 3
        self.pause_bars_size_y = 6

    def load(self, app, args):
        pass

    def update(self, app):
        # Text Scrolling

        # Pause Button
        button_x = app.screen_left.x + (
            (self.pause_button_size + self.pause_button_padding) * app.scale
        )
        button_y = app.screen_bottom.y + (
            (self.pause_button_size + self.pause_button_padding) * app.scale
        )
        hover = (
            distance(app.mouse_pos, V(button_x, button_y))
            < self.pause_button_size * app.scale
        )
        if hover:
            if app.mouse_pressed_primary:
                app.set_screen(Screen.PAUSED)
        # Back Button
        hover = is_point_in_rect(
            app.mouse_pos,
            V(app.screen_right.x, app.screen_bottom.y),
            V(
                app.screen_right.x - (130 * app.scale),
                app.screen_bottom.y + (40 * app.scale),
            ),
        )
        if hover:
            if app.mouse_pressed_primary:
                app.set_screen(Screen.PLAYING)
                app.game = Game(app.gods[self.selection_list.selected_index])

    def draw(self, app):
        scene = app.game.god.tree.scenes[app.game.current_scene_index]
        scene_text = scene.text
        scene_image = scene.image
        text_font = app.main_font.new_size(int(app.main_font.size * app.scale))
        text_x = -230 * app.scale
        text_y = 35 * app.scale
        text_wrap_distance = max(
            1, int(abs(app.screen_right.x - text_x - (10 * app.scale)))
        )
        text_bottom_y = (
            self.pause_button_padding
            + self.pause_button_size
            + self.pause_button_padding
        )
        # Text

        # Scene Image
        if scene_image is not None:
            app.draw_image(
                scene_image,
                V(0 * app.scale, 110 * app.scale),
                origin=Origin.CENTER,
                scale_x=app.scale,
                scale_y=app.scale,
                antialiasing=False,
            )
        # Pause Button
        button_x = app.screen_left.x + (
            (self.pause_button_size + self.pause_button_padding) * app.scale
        )
        button_y = app.screen_bottom.y + (
            (self.pause_button_size + self.pause_button_padding) * app.scale
        )
        hover = (
            distance(app.mouse_pos, V(button_x, button_y))
            < self.pause_button_size * app.scale
        )
        app.fill_circle(
            V(button_x, button_y),
            self.pause_button_size * app.scale,
            Color(50, 50, 50) if hover else Color(40, 40, 40),
        )
        # Left Bar
        app.draw_line(
            V(
                button_x + (self.pause_bars_size_x * app.scale),
                button_y + (self.pause_bars_size_y * app.scale),
            ),
            V(
                button_x + (self.pause_bars_size_x * app.scale),
                button_y - (self.pause_bars_size_y * app.scale),
            ),
            Color(255, 255, 255),
            int(2 * app.scale),
        )
        # Right Bar
        app.draw_line(
            V(
                button_x - (self.pause_bars_size_x * app.scale),
                button_y + (self.pause_bars_size_y * app.scale),
            ),
            V(
                button_x - (self.pause_bars_size_x * app.scale),
                button_y - (self.pause_bars_size_y * app.scale),
            ),
            Color(255, 255, 255),
            int(2 * app.scale),
        )

        # Back Button
