import math
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


def within_button(mouse_pos, a, b):
    return within(mouse_pos.x, a.x, b.x) and within(mouse_pos.y, a.y, b.y)


def split_to_lines(text: str):
    return [line for line in text.splitlines() if line.strip()]


BASE_PATH = os.path.dirname(os.path.abspath(__file__))


def asset(path):
    return str(os.path.join(BASE_PATH, "assets", path))


class State(Enum):
    INTRO = 1
    CREDITS = 2
    QUIT = 3

    MAIN_MENU = 4
    NEW_GAME = 5
    LOAD_GAME_MENU = 6
    SETTINGS_MENU = 7

    PLAYING = 8
    PAUSED = 9
    LOAD_GAME_PLAYING = 10
    SETTINGS_PLAYING = 11


class Link:
    def __init__(self, link, text):
        self.link = link
        self.text = text


class Screen:
    def __init__(self, encoded: str):
        lines = split_to_lines(encoded)
        links = []
        for line in lines:
            if line.startswith("title: "):
                self.title = line.removeprefix("title: ")
            elif line.startswith("text: "):
                self.text = line.removeprefix("text: ")
            else:
                screen, text = line.split(": ")
                links.append(Link(screen, text))


class Tree:
    def __init__(self, encoded):
        self.screens = {}


class God:
    def __init__(self, encoded: str):
        lines = split_to_lines(encoded)

        for line in lines:

            if line.startswith("name: "):
                self.name = line.removeprefix("name: ")
            elif line.startswith("info: "):
                self.info = line.removeprefix("info: ")
            elif line.startswith("image: "):
                self.image = line.removeprefix("image: ")
            elif line == "#tree":
                break

        self.tree = Tree(encoded)


class Game:
    def __init__(self, god: God):
        self.god = god
        self.current_screen = None


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

    def _load_data(self):
        gods_folder = asset("data/gods")

        self.gods_text = []

        for name in os.listdir(gods_folder):
            path = os.path.join(gods_folder, name)
            if os.path.isfile(path) and name.lower().endswith(".txt"):
                with open(path, "r", encoding="utf-8") as f:
                    self.gods_text.append(f.read())

        self.gods = [God(i) for i in self.gods_text]

    def _initialize_intro(self):
        self.intro_pre_delay = 1.5
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

    def _initialize_main_menu(self):
        self.main_menu_button_top_offset = 10
        self.main_menu_button_width = 200
        self.main_menu_button_height = 60
        self.main_menu_button_padding = 10
        self.main_menu_button_color = Color(50, 70, 50)
        self.main_menu_button_hover_color = Color(60, 80, 100)
        self.main_menu_button_outline_thickness = 2 * self.scale
        self.main_menu_button_outline_color = Color(0, 50, 0)
        self.main_menu_button_roundness = 10
        self.main_menu_button_text_color = Color(255, 255, 255)
        self.main_menu_button_text_font = self.main_font

    def _initialize_new_game(self):
        self.new_game_selected_god = 0

    def initialize(self):
        self.scale = 1.0
        self.state = State.INTRO
        self.seconds_since_start = 0.0
        self.mouse_down_primary_last_frame = False

        self._load_assets()
        self._initialize_intro()
        self._initialize_main_menu()
        self._load_data()
        self._initialize_new_game()

        self.game = None  # Will be initialized properly in State.NEW_GAME

    def update(self):
        mouse_pressed = (
            self.mouse_down_primary and not self.mouse_down_primary_last_frame
        )

        scale_x = self.width / self._original_width
        scale_y = self.height / self._original_height
        self.scale = (scale_x + scale_y) / 2.0

        self.seconds_since_start += self.deltatime

        if self.state == State.QUIT:
            quit()

        elif self.state == State.INTRO:
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

        elif self.state == State.MAIN_MENU:
            buttons = [
                State.NEW_GAME,
                State.LOAD_GAME_MENU,
                State.SETTINGS_MENU,
                State.CREDITS,
                State.QUIT,
            ]
            for i, button in enumerate(buttons):
                x = 0
                y = (
                    self.screen_top
                    - (
                        (
                            self.main_menu_button_top_offset
                            + self.main_menu_button_height / 2
                        )
                        + (
                            i
                            * (
                                self.main_menu_button_height
                                + self.main_menu_button_padding
                            )
                        )
                    )
                    * self.scale
                )
                width = self.main_menu_button_width * self.scale
                height = self.main_menu_button_height * self.scale

                ax = x - width / 2
                ay = y - height / 2
                bx = x + width / 2
                by = y + height / 2

                hover = within_button(self.mouse_pos, V(ax, ay), V(bx, by))

                if hover and mouse_pressed:
                    self.state = button

        elif self.state == State.NEW_GAME:
            # God list selection
            for i, god in enumerate(self.gods):
                hover = within_button(
                    self.mouse_pos,
                    V(
                        self.screen_left + (1 * self.scale),
                        self.screen_top - (1 * self.scale) - (i * 25 * self.scale),
                    ),
                    V(
                        self.screen_left + (149 * self.scale),
                        self.screen_top
                        - (1 * self.scale)
                        - (i * 25 * self.scale)
                        - (25 * self.scale),
                    ),
                )
                if hover and mouse_pressed:
                    self.new_game_selected_god = i

            # Start button
            hover = within_button(
                self.mouse_pos,
                V(self.screen_right, self.screen_bottom),
                V(
                    self.screen_right - (130 * self.scale),
                    self.screen_bottom + (40 * self.scale),
                ),
            )

            if hover:
                if mouse_pressed:
                    self.game = Game(self.gods[self.new_game_selected_god])
                    self.state = State.PLAYING

        elif self.state == State.PLAYING:
            hover = within_button(
                self.mouse_pos,
                V(self.screen_left, self.screen_bottom),
                V(
                    self.screen_left + (30 * self.scale),
                    self.screen_bottom + (30 * self.scale),
                ),
            )
            if hover:
                if mouse_pressed:
                    self.state = State.PAUSED

        elif self.state == State.PAUSED:
            buttons = [
                State.PLAYING,
                State.LOAD_GAME_PLAYING,
                State.LOAD_GAME_PLAYING,
                State.SETTINGS_PLAYING,
                State.MAIN_MENU,
            ]
            for i, button in enumerate(buttons):
                x = 0
                y = (
                    self.screen_top
                    - (
                        (
                            self.main_menu_button_top_offset
                            + self.main_menu_button_height / 2
                        )
                        + (
                            i
                            * (
                                self.main_menu_button_height
                                + self.main_menu_button_padding
                            )
                        )
                    )
                    * self.scale
                )
                width = self.main_menu_button_width * self.scale
                height = self.main_menu_button_height * self.scale

                ax = x - width / 2
                ay = y - height / 2
                bx = x + width / 2
                by = y + height / 2

                hover = within_button(self.mouse_pos, V(ax, ay), V(bx, by))

                if hover and mouse_pressed:
                    self.state = button

        self.mouse_down_primary_last_frame = self.mouse_down_primary

    def draw(self):
        self.clear(Color(0, 0, 0))

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
            buttons = ["New Game", "Load Game", "Settings", "Credits", "Quit"]
            for i, button in enumerate(buttons):
                x = 0
                y = (
                    self.screen_top
                    - (
                        (
                            self.main_menu_button_top_offset
                            + self.main_menu_button_height / 2
                        )
                        + (
                            i
                            * (
                                self.main_menu_button_height
                                + self.main_menu_button_padding
                            )
                        )
                    )
                    * self.scale
                )
                width = self.main_menu_button_width * self.scale
                height = self.main_menu_button_height * self.scale

                ax = x - width / 2
                ay = y - height / 2
                bx = x + width / 2
                by = y + height / 2

                hover = within_button(self.mouse_pos, V(ax, ay), V(bx, by))

                self.fill_rounded_rect(
                    V(ax, ay),
                    V(bx, by),
                    (
                        self.main_menu_button_hover_color
                        if hover
                        else self.main_menu_button_color
                    ),
                    int(self.main_menu_button_outline_thickness),
                    self.main_menu_button_outline_color,
                    self.main_menu_button_roundness,
                    self.main_menu_button_roundness,
                    self.main_menu_button_roundness,
                    self.main_menu_button_roundness,
                    1,
                )

                self.draw_text(
                    button,
                    V(x, y),
                    self.main_menu_button_text_font.new_size(int(40 * self.scale)),
                    self.main_menu_button_text_color,
                    Origin.CENTER,
                )

        elif self.state == State.NEW_GAME:
            # God list
            self.fill_rect(
                V(self.screen_left, self.screen_top),
                V(self.screen_left + (150 * self.scale), self.screen_bottom),
                Color(30, 30, 30),
                int(2 * self.scale),
                Color(50, 50, 50),
            )

            # God image
            self.fill_rect(
                V(self.screen_right, self.screen_top),
                V(
                    self.screen_right - (130 * self.scale),
                    self.screen_top - (150 * self.scale),
                ),
                Color(30, 30, 30),
                int(2 * self.scale),
                Color(50, 50, 50),
            )

            # God name and stats
            self.fill_rect(
                V(self.screen_left + (150 * self.scale), self.screen_top),
                V(
                    self.screen_right - (130 * self.scale),
                    self.screen_top - (150 * self.scale),
                ),
                Color(0, 0, 0),
            )

            # God lore
            self.fill_rect(
                V(
                    self.screen_left + (150 * self.scale),
                    self.screen_top - (150 * self.scale),
                ),
                V(self.screen_right, self.screen_bottom),
                Color(0, 0, 0),
            )

            # Gods list
            for i, god in enumerate(self.gods):
                hover = within_button(
                    self.mouse_pos,
                    V(
                        self.screen_left + (1 * self.scale),
                        self.screen_top - (1 * self.scale) - (i * 25 * self.scale),
                    ),
                    V(
                        self.screen_left + (149 * self.scale),
                        self.screen_top
                        - (1 * self.scale)
                        - (i * 25 * self.scale)
                        - (25 * self.scale),
                    ),
                )

                if hover and self.new_game_selected_god == i:
                    color = Color(60, 60, 60)
                elif hover:
                    color = Color(50, 50, 50)
                elif self.new_game_selected_god == i:
                    color = Color(50, 50, 50)
                else:
                    color = Color(40, 40, 40)

                self.fill_rect(
                    V(
                        self.screen_left + (1 * self.scale),
                        self.screen_top - (1 * self.scale) - (i * 25 * self.scale),
                    ),
                    V(
                        self.screen_left + (149 * self.scale),
                        self.screen_top
                        - (1 * self.scale)
                        - (i * 25 * self.scale)
                        - (25 * self.scale),
                    ),
                    color,
                )

                self.draw_text(
                    god.name,
                    V(
                        self.screen_left + (55 * self.scale) - (3 * self.scale),
                        self.screen_top - (25 * self.scale * i) + (3 * self.scale),
                    ),
                    self.main_font.new_size(int(30 * self.scale)),
                    Color(200, 255, 200),
                    Origin.TOPRIGHT,
                )

            # God image
            selected_god = self.gods[self.new_game_selected_god]
            try:
                self.draw_image(
                    Image(
                        asset(
                            f"images/god/{selected_god.image}/{selected_god.image}.png"
                        )
                    ),
                    V(
                        self.screen_right - (65 * self.scale),
                        self.screen_top - (75 * self.scale),
                    ),
                    origin=Origin.CENTER,
                    scale_x=self.scale
                    * 1.5
                    * (math.sin(self.seconds_since_start * 2) * 0.1 + 0.9),
                    scale_y=self.scale * 1.5,
                    antialiasing=True,
                )
            except Exception:
                raise Exception(f"Failed to load image for god '{
                    selected_god.name}' at path: {
                    asset(
                        f'images/god/{
                            selected_god.image}/{
                            selected_god.image}.png')}")

            # God name
            self.draw_text(
                selected_god.name,
                V(
                    self.screen_left + (155 * self.scale) + (3 * self.scale),
                    self.screen_top + (5 * self.scale),
                ),
                self.heading_font.new_size(int(40 * self.scale)),
                Color(255, 255, 255),
                Origin.TOPLEFT,
            )

            # God lore
            self.draw_text(
                selected_god.info,
                V(
                    self.screen_left + (155 * self.scale) + (3 * self.scale),
                    self.screen_top - (155 * self.scale) + (3 * self.scale),
                ),
                self.main_font.new_size(int(30 * self.scale)),
                Color(255, 255, 255),
                Origin.TOPLEFT,
                wrap_distance=abs(
                    self.screen_left
                    - (self.screen_left + (155 * self.scale) + (3 * self.scale))
                )
                * 2,
            )

            # Start button
            hover = within_button(
                self.mouse_pos,
                V(self.screen_right, self.screen_bottom),
                V(
                    self.screen_right - (130 * self.scale),
                    self.screen_bottom + (40 * self.scale),
                ),
            )

            self.fill_rect(
                V(self.screen_right, self.screen_bottom),
                V(
                    self.screen_right - (130 * self.scale),
                    self.screen_bottom + (40 * self.scale),
                ),
                Color(40, 40, 40) if hover else Color(30, 30, 30),
                int(2 * self.scale),
                Color(50, 50, 50),
            )

            self.draw_text(
                "Start Game",
                V(
                    self.screen_right - (65 * self.scale),
                    self.screen_bottom + (20 * self.scale),
                ),
                self.main_font.new_size(int(30 * self.scale)),
                Color(255, 255, 255),
                Origin.CENTER,
            )

        elif self.state == State.PLAYING:
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

            # Pause button
            hover = within_button(
                self.mouse_pos,
                V(self.screen_left, self.screen_bottom),
                V(
                    self.screen_left + (30 * self.scale),
                    self.screen_bottom + (30 * self.scale),
                ),
            )
            self.fill_rounded_rect(
                V(self.screen_left, self.screen_bottom),
                V(
                    self.screen_left + (30 * self.scale),
                    self.screen_bottom + (30 * self.scale),
                ),
                Color(40, 40, 40) if hover else Color(30, 30, 30),
                top_right_roundness=30 * self.scale,
                steps=10,
            )
            self.draw_text(
                "||",
                V(
                    self.screen_left + (15 * self.scale),
                    self.screen_bottom + (15 * self.scale),
                ),
                self.main_font.new_size(int(20 * self.scale)),
                Color(255, 255, 255),
                Origin.CENTER,
            )

        elif self.state == State.PAUSED:
            buttons = ["Resume", "Load Game", "Save Game", "Settings", "Exit Game"]
            for i, button in enumerate(buttons):
                x = 0
                y = (
                    self.screen_top
                    - (
                        (
                            self.main_menu_button_top_offset
                            + self.main_menu_button_height / 2
                        )
                        + (
                            i
                            * (
                                self.main_menu_button_height
                                + self.main_menu_button_padding
                            )
                        )
                    )
                    * self.scale
                )
                width = self.main_menu_button_width * self.scale
                height = self.main_menu_button_height * self.scale

                ax = x - width / 2
                ay = y - height / 2
                bx = x + width / 2
                by = y + height / 2

                hover = within_button(self.mouse_pos, V(ax, ay), V(bx, by))

                self.fill_rounded_rect(
                    V(ax, ay),
                    V(bx, by),
                    (
                        self.main_menu_button_hover_color
                        if hover
                        else self.main_menu_button_color
                    ),
                    int(self.main_menu_button_outline_thickness),
                    self.main_menu_button_outline_color,
                    self.main_menu_button_roundness,
                    self.main_menu_button_roundness,
                    self.main_menu_button_roundness,
                    self.main_menu_button_roundness,
                    1,
                )

                self.draw_text(
                    button,
                    V(x, y),
                    self.main_menu_button_text_font.new_size(int(40 * self.scale)),
                    self.main_menu_button_text_color,
                    Origin.CENTER,
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
