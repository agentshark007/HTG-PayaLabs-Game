import os
from enum import Enum
from pgiud import *

BASE_PATH = os.path.dirname(os.path.abspath(__file__))


def asset(path):
    return str(os.path.join(BASE_PATH, "assets", path))


class State(Enum):
    INTRO = 1
    MAIN_MENU = 2
    NEW_GAME = 3
    LOAD_GAME_MENU = 4
    SETTINGS = 5
    PLAYING = 6
    LOAD_GAME_PLAYING = 7
    CREDITS = 8


class App(Window):
    def __init__(self):
        super().__init__(
            width=480,
            height=360,
            title="HTG PayaLabs Game",
            resizable=Resizable.ASPECT,
            origin=Origin.CENTER,
        )

    def initialize(self):
        self.test_scene = Image(asset("images/scene/trees.png"))

        self.heading_font = Font(asset("fonts/Silkscreen-Regular.ttf"))
        self.main_font = Font(asset("fonts/VT323-Regular.ttf"))

        self.scale = 1.0

        self.state = State.INTRO

    def update(self):
        scale_x = self.width / self._original_width
        scale_y = self.height / self._original_height
        self.scale = (scale_x + scale_y) / 2.0

        if self.state == State.INTRO:
            self.intro_timer = self.intro_timer + self.deltatime if hasattr(self, "intro_timer") else 0.0
            if self.intro_timer >= 3.0:  # After 3 seconds, switch to the main menu
                self.state = State.PLAYING

        elif self.state == State.MAIN_MENU:
            pass

        elif self.state == State.LOAD_GAME_MENU:
            pass

        elif self.state == State.SETTINGS:
            pass

        elif self.state == State.PLAYING:
            pass

        elif self.state == State.LOAD_GAME_PLAYING:
            pass

        elif self.state == State.CREDITS:
            pass

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
            self.clear(Color(0, 0, 0))  # Black background

            # Context image
            self.draw_image(
                self.test_scene,
                V(0 * self.scale, 110 * self.scale),
                origin=Origin.CENTER,
                scale_x=self.scale,
                scale_y=self.scale,
                antialiasing=False,
            )

            # Heading text
            self.draw_text(
                "Heading text",
                V(-230 * self.scale, 40 * self.scale),
                font=self.heading_font.new_size(
                    int(self.heading_font.size * self.scale)
                ),
                color=Color(255, 255, 255),
                origin=Origin.TOPLEFT,
            )

            # Main text
            self.draw_text(
                "Main text. The quick brown fox jumps over the lazy dog.",
                V(-230 * self.scale, 10 * self.scale),
                self.main_font.new_size(int(self.main_font.size * self.scale)),
                Color(255, 255, 255),
                Origin.TOPLEFT,
            )

        elif self.state == State.LOAD_GAME_PLAYING:
            pass

        elif self.state == State.CREDITS:
            pass


def main():
    App().start()


if __name__ == "__main__":
    main()
