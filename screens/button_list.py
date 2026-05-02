from pgiud import *
from utility import *


class ButtonList:
    def initialize(self, app):
        self.title_top_offset = 25
        self.title_font_size = 40
        self.button_top_offset = 60
        self.button_width = 180
        self.button_height = 50
        self.button_padding = 10
        self.button_color = Color(50, 70, 50)
        self.button_hover_color = Color(60, 80, 100)
        self.button_outline_thickness = 2
        self.button_outline_color = Color(0, 50, 0)
        self.button_roundness = 10
        self.button_text_color = Color(255, 255, 255)
        self.button_text_font_size = 40
        self.title_text_color = Color(255, 255, 255)

    def update(self, app, buttons):
        pass

    def draw(self, app, title, buttons):
        if len(buttons) == 5:
            for i, button in enumerate(buttons):
                x = 0
                y = app.screen_top.y - (
                    (
                        (self.button_top_offset + self.button_height / 2)
                        + (i * (self.button_height + self.button_padding))
                    )
                    * app.scale
                )
                width = self.button_width * app.scale
                height = self.button_height * app.scale
                ax = x - width / 2
                ay = y - height / 2
                bx = x + width / 2
                by = y + height / 2
                hover = is_point_in_rect(app.mouse_pos, V(ax, ay), V(bx, by))
                app.fill_rounded_rect(
                    V(ax, ay),
                    V(bx, by),
                    self.button_hover_color if hover else self.button_color,
                    int(self.button_outline_thickness * app.scale),
                    self.button_outline_color,
                    self.button_roundness * app.scale,
                    self.button_roundness * app.scale,
                    self.button_roundness * app.scale,
                    self.button_roundness * app.scale,
                    1,
                )
                app.draw_text(
                    button,
                    V(x, y),
                    app.main_font.new_size(self.button_text_font_size * app.scale),
                    self.button_text_color,
                    Origin.CENTER,
                )
        app.draw_text(
            title,
            V(
                app.screen_center.x,
                app.screen_top.y - (self.title_top_offset * app.scale),
            ),
            app.heading_font.new_size(self.title_font_size * app.scale),
            self.title_text_color,
            Origin.CENTER,
        )
