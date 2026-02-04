import os
from enum import Enum

import pgiud

BASE_PATH = os.path.dirname(os.path.abspath(__file__))


def asset(path):
    return os.path.join(BASE_PATH, "assets", path)


class State(Enum):
    INTRO = 1
    MAIN_MENU = 2
    NEW_GAME = 3
    LOAD_GAME_MENU = 4
    SETTINGS = 5
    PLAYING = 6
    LOAD_GAME_PLAYING = 7
    CREDITS = 8


class App(pgiud.Window):
    def __init__(self):
        super().__init__(
            width=480,
            height=360,
            title="HTG PayaLabs Game",
            resizable=pgiud.Resizable.ASPECT,
            origin=pgiud.Origin.CENTER,
        )

    def initialize(self):
        self.test_scene = pgiud.Image(asset("images/scene/trees.png"))

        self.heading_font = pgiud.Font(asset("fonts/Silkscreen-Regular.ttf"))
        self.main_font = pgiud.Font(asset("fonts/VT323-Regular.ttf"))

        self.scale = 1.0

        self.state = State.PLAYING

    def update(self):
        scalex = self.width / self._original_width
        scaley = self.height / self._original_height
        self.scale = (scalex + scaley) / 2.0

    def draw(self):
        if self.state == State.INTRO:
            pass

        elif self.state == State.MAIN_MENU:
            pass

        elif self.state == State.LOAD_GAME_MENU:
            pass

        elif self.state == State.SETTINGS:
            pass

        elif self.state == State.PLAYING:
            self.clear(pgiud.Color(0, 0, 0))  # Black background

            # Context image
            self.draw_image(
                self.test_scene,
                0 * self.scale,
                110 * self.scale,
                origin=pgiud.Origin.CENTER,
                scalex=self.scale,
                scaley=self.scale,
                antialiasing=False,
            )

            # Heading text
            self.draw_text(
                "Heading text",
                -230 * self.scale,
                40 * self.scale,
                self.heading_font.new_size(self.heading_font.size * self.scale),
                pgiud.Color(255, 255, 255),
                pgiud.Origin.TOPLEFT,
            )

            # Main text
            self.draw_text(
                "Main text. The quick brown fox jumps over the lazy dog.",
                -230 * self.scale,
                10 * self.scale,
                self.main_font.new_size(self.main_font.size * self.scale),
                pgiud.Color(255, 255, 255),
                pgiud.Origin.TOPLEFT,
            )

        elif self.state == State.LOAD_GAME_PLAYING:
            pass

        elif self.state == State.CREDITS:
            pass


def main():
    App().start()


if __name__ == "__main__":
    main()
