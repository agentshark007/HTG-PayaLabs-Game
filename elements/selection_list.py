from pgiud import *
from utility import *


class SelectionList:
    def initialize(self, app, title, items, item_label, empty_text, width=150):
        self.selected_index = -1
        self.title = title
        self.items = items
        self.item_label = item_label
        self.empty_text = empty_text
        self.width = width

    def _selection_item_rect(self, app, index: int):
        return (
            V(
                app.screen_left.x + (1 * app.scale),
                app.screen_top.y
                - (1 * app.scale)
                - (index * 25 * app.scale)
                - (30 * app.scale),
            ),
            V(
                app.screen_left.x + ((self.width - 1) * app.scale),
                app.screen_top.y
                - (1 * app.scale)
                - (index * 25 * app.scale)
                - (25 * app.scale)
                - (30 * app.scale),
            ),
        )

    def update(self, app):
        for i, _item in enumerate(self.items):
            a, b = self._selection_item_rect(app, i)
            hover = is_point_in_rect(app.mouse_pos, a, b)
            if hover and app.mouse_pressed:
                self.selected_index = i
        if self.selected_index >= len(self.items):
            self.selected_index = -1

    def draw(self, app):
        app.fill_rect(
            V(app.screen_left.x, app.screen_top.y),
            V(app.screen_left.x + (self.width * app.scale), app.screen_bottom.y),
            Color(30, 30, 30),
            int(2 * app.scale),
            Color(50, 50, 50),
        )
        app.draw_text(
            self.title,
            V(
                app.screen_left.x + ((self.width / 2) * app.scale),
                app.screen_top.y - (15 * app.scale),
            ),
            app.main_font.new_size(int(23 * app.scale)),
            Color(255, 255, 255),
            Origin.CENTER,
        )
        if not self.items:
            app.draw_text(
                self.empty_text,
                V(
                    app.screen_left.x + ((self.width / 2) * app.scale),
                    app.screen_top.y - (55 * app.scale),
                ),
                app.main_font.new_size(int(18 * app.scale)),
                Color(180, 180, 180),
                Origin.CENTER,
            )
            return
        for i, item in enumerate(self.items):
            a, b = self._selection_item_rect(app, i)
            hover = is_point_in_rect(app.mouse_pos, a, b)
            if hover and self.selected_index == i:
                color = Color(60, 60, 60)
            elif hover:
                color = Color(50, 50, 50)
            elif self.selected_index == i:
                color = Color(50, 50, 50)
            else:
                color = Color(40, 40, 40)
            app.fill_rect(a, b, color)
            app.draw_text(
                self.item_label(item),
                V(
                    app.screen_left.x + ((self.width / 2) * app.scale),
                    app.screen_top.y - (25 * app.scale * i) - (30 * app.scale),
                ),
                app.main_font.new_size(int(23 * app.scale)),
                Color(200, 220, 200),
                Origin.TOP,
            )
