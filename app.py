import os
from enum import Enum

from pgiud import *


def within(x, a, b):
    if a == b:
        if x == a:
            return True
        else:
            return False

    elif a > b:
        if b < x < a:
            return True
        else:
            return False

    elif a < b:
        if a < x < b:
            return True
        else:
            return False

    else:
        return False


BASE_PATH = os.path.dirname(os.path.abspath(__file__))


def asset(path):
    return str(os.path.join(BASE_PATH, "assets", path))


class State(Enum):
    INTRO = 1
    CREDITS = 2

    MAIN_MENU = 3
    NEW_GAME = 4
    LOAD_GAME_MENU = 5
    SETTINGS_MENU = 6

    PLAYING = 7
    PAUSED = 8
    LOAD_GAME_PLAYING = 9


class App(Window):
    def __init__(self):
        super().__init__(
            width=480,
            height=360,
            title="HTG PayaLabs Game",
            resizable=Resizable.ASPECT,
            origin=Origin.CENTER,
        )

    def _load_assets(self):
        # Scenes
        self.trees_scene = Image(asset("images/scene/trees.png"))

        # Fonts
        self.heading_font = Font(asset("fonts/Silkscreen-Regular.ttf"))
        self.main_font = Font(asset("fonts/VT323-Regular.ttf"))

        # Intro logos and sound
        self.intro_payalabs_logo = Image(asset("images/intro/payalabs.png"))
        self.intro_pgiud_logo = Image(asset("images/intro/pgiud.png"))
        self.intro_pygame_logo = Image(asset("images/intro/pygame.png"))
        self.intro_boom_sound = Sound(asset("sounds/intro_boom.mp3"))

    def _initialize_intro(self):
        self.intro_pre_delay = 3.0
        self.intro_logo_time = 1.0
        self.intro_post_delay = 2.0

        self.intro_current_logo_index = (
            0  # 0=pre-delay, 1=payalabs, 2=pgiud, 3=pygame, 4=post-delay
        )
        self.intro_current_logo_time = 0

        self.intro_logos = [
            self.intro_payalabs_logo,
            self.intro_pgiud_logo,
            self.intro_pygame_logo,
        ]

    def initialize(self):
        self.scale = 1.0
        self.state = State.MAIN_MENU

        self._load_assets()
        self._initialize_intro()

    def update(self):
        scale_x = self.width / self._original_width
        scale_y = self.height / self._original_height
        self.scale = (scale_x + scale_y) / 2.0

        if self.state == State.INTRO:
            self.intro_current_logo_time += self.deltatime
            num_logos = len(self.intro_logos)

            if self.intro_current_logo_index == 0:
                if self.intro_current_logo_time > self.intro_pre_delay:
                    self.intro_current_logo_index = 1
                    self.intro_current_logo_time = 0
                    try:
                        if self.intro_boom_sound:
                            self.intro_boom_sound.play()
                    except Exception:
                        pass

            elif 1 <= self.intro_current_logo_index <= num_logos:
                if self.intro_current_logo_time > self.intro_logo_time:
                    self.intro_current_logo_index += 1
                    self.intro_current_logo_time = 0
                    if 1 <= self.intro_current_logo_index <= num_logos:
                        try:
                            if self.intro_boom_sound:
                                self.intro_boom_sound.play()
                        except Exception:
                            pass

            elif self.intro_current_logo_index == num_logos + 1:
                if self.intro_current_logo_time > self.intro_post_delay:
                    self.state = State.MAIN_MENU

        elif self.state == State.PLAYING:
            pass

    def draw(self):
        self.clear(Color(0, 0, 0, 255))

        if self.state == State.INTRO:
            num_logos = len(self.intro_logos)
            idx = self.intro_current_logo_index

            if 1 <= idx <= num_logos:
                img = self.intro_logos[idx - 1]

                total = self.intro_logo_time
                t = self.intro_current_logo_time
                fade = min(0.3, total / 2.0)

                if total <= 0 or t <= 0:
                    alpha = 255
                elif t < fade:
                    alpha = int(255 * (t / fade))
                elif t > total - fade:
                    alpha = int(255 * ((total - t) / fade))
                else:
                    alpha = 255

                alpha = max(0, min(255, alpha))

                logo_scale = self.scale * 0.15
                try:
                    self.draw_image(
                        img,
                        V(self.screen_center_x, self.screen_center_y),
                        origin=Origin.CENTER,
                        image_filter=Color(255, 255, 255, alpha),
                        scale_x=logo_scale,
                        scale_y=logo_scale,
                        antialiasing=True,
                    )
                except Exception:
                    pass
            else:
                # index 0 = pre-delay, index num_logos+1 = post-delay: draw
                # nothing
                pass

        elif self.state == State.MAIN_MENU:
            button_top_offset = 10
            button_width = 200
            button_height = 60
            button_padding = 10
            button_color = Color(50, 70, 50)
            button_hover_color = Color(60, 80, 100)
            button_outline_thickness = 2 * self.scale
            button_outline_color = Color(0, 50, 0)
            button_roundness = 10

            button_text_font = self.main_font.new_size(int(40 * self.scale))
            button_text_color = Color(255, 255, 255)

            buttons = ["New Game", "Load Game", "Settings", "Credits", "Quit"]
            for i, button in enumerate(buttons):
                x = 0
                y = (
                    self.screen_top
                    - (
                        (button_top_offset + button_height / 2)
                        + (i * (button_height + button_padding))
                    )
                    * self.scale
                )
                width = button_width * self.scale
                height = button_height * self.scale

                ax = x - width / 2
                ay = y - height / 2
                bx = x + width / 2
                by = y + height / 2

                hover = within(self.mouse_pos.x, ax, bx) and within(
                    self.mouse_pos.y, ay, by
                )

                self.fill_rounded_rect(
                    V(ax, ay),
                    V(bx, by),
                    button_hover_color if hover else button_color,
                    int(button_outline_thickness),
                    button_outline_color,
                    button_roundness,
                    button_roundness,
                    button_roundness,
                    button_roundness,
                )

                self.draw_text(
                    button, V(x, y), button_text_font, button_text_color, Origin.CENTER
                )

        elif self.state == State.PLAYING:
            # Black background
            self.clear(Color(0, 0, 0))

            # Context image
            self.draw_image(
                self.trees_scene,
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

    def on_quit(self):
        try:
            self.intro_boom_sound.stop()
        except Exception:
            pass


def main():
    App().start()


if __name__ == "__main__":
    main()
