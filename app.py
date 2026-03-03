import math
import os
import sys
from enum import Enum

from pgiud import *


def is_between(x, a, b):
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


def is_point_in_rect(point, a, b):
    return is_between(point.x, a.x, b.x) and is_between(point.y, a.y, b.y)


def split_nonempty_lines(text: str):
    return [line for line in text.splitlines() if line.strip()]


def distance(a, b):
    return math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def get_asset_path(path):
    return str(os.path.join(BASE_DIR, "assets", path))


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
    def __init__(self, target, label):
        self.target = target
        self.label = label


class Screen:
    def __init__(self, encoded: str, screen_id: str = None):
        # Each Screen now carries an id, title, text and links list
        self.id = screen_id
        lines = split_nonempty_lines(encoded)
        links = []
        self.title = ""
        self.text = ""
        for line in lines:
            if line.startswith("title: "):
                self.title = line[len("title: ") :].strip()
            elif line.startswith("text: "):
                self.text = line[len("text: ") :].strip()
            else:
                # Assumes any other line is a link: "<screen_id>: <link text>"
                # Use partition to avoid exceptions if the line is malformed
                if ": " in line:
                    target, _, link_text = line.partition(": ")
                    links.append(Link(target.strip(), link_text.strip()))
                else:
                    # Unknown line format: ignore or append to text
                    # We'll append to text to preserve any stray lines
                    if self.text:
                        self.text += "\n" + line.strip()
                    else:
                        self.text = line.strip()
        self.links = links


class Tree:
    def __init__(self, encoded):
        lines = split_nonempty_lines(encoded)
        screens = []
        ready = False
        screen_text = ""
        screen_id = None  # To track the screen IDs
        first_screen_index = None  # To store the first screen's index
        for line in lines:
            if line.startswith("#tree"):
                ready = True
                continue
            if not ready:
                continue
            if line.startswith("##"):  # This signifies a new screen
                # If we were building a previous screen, append it
                if screen_id is not None:
                    screens.append(Screen(screen_text, screen_id))
                # Start a new screen
                screen_id = line.removeprefix("##").strip()
                screen_text = ""
                # If this is the first screen we've seen, record its index
                if first_screen_index is None:
                    first_screen_index = len(screens)
            else:
                screen_text += line + "\n"
        # Add the last screen if present
        if screen_id is not None and screen_text:
            screens.append(Screen(screen_text, screen_id))
        self.screens = screens
        # If no explicit first index was captured, default to 0
        self.first_screen_index = (
            first_screen_index if first_screen_index is not None else 0
        )


class God:
    def __init__(self, encoded: str):
        lines = split_nonempty_lines(encoded)
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
        # Set starting screen index from tree
        self.start_screen_index = self.tree.first_screen_index


class Game:
    def __init__(self, god: God):
        self.god = god
        # current_screen_index is an integer index into god.tree.screens
        self.current_screen_index = god.start_screen_index


class App(Window):
    def __init__(self):
        super().__init__(
            width=480,
            height=360,
            title="Fate of the Gods",
            resizable=Resizable.ASPECT,
            origin=Origin.CENTER,
        )

    def _load_assets(self):
        # Scenes
        self.trees_scene = Image(get_asset_path("images/scene/trees.png"))
        # Fonts
        self.heading_font = Font(get_asset_path("fonts/Silkscreen-Regular.ttf"))
        self.main_font = Font(get_asset_path("fonts/VT323-Regular.ttf"))
        # Intro logos and sound
        self.intro_payalabs_logo = Image(get_asset_path("images/intro/payalabs.png"))
        self.intro_pgiud_logo = Image(get_asset_path("images/intro/pgiud.png"))
        self.intro_pygame_logo = Image(get_asset_path("images/intro/pygame.png"))
        self.intro_boom_sound = Sound(get_asset_path("sounds/intro_boom.mp3"))

    def _load_data(self):
        gods_folder = get_asset_path("data/gods")
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

    def _initialize_button_list_settings(self):
        self.button_list_title_top_offset = 25
        self.button_list_title_font = self.heading_font.new_size(int(40 * self.scale))
        self.button_list_button_top_offset = 60
        self.button_list_button_width = 180
        self.button_list_button_height = 50
        self.button_list_button_padding = 10
        self.button_list_button_color = Color(50, 70, 50)
        self.button_list_button_hover_color = Color(60, 80, 100)
        self.button_list_button_outline_thickness = 2 * self.scale
        self.button_list_button_outline_color = Color(0, 50, 0)
        self.button_list_button_roundness = 10
        self.button_list_button_text_color = Color(255, 255, 255)
        self.button_list_button_text_font = self.main_font.new_size(
            int(40 * self.scale)
        )

    def _initialize_new_game(self):
        self.new_game_selected_god = 0

    def initialize(self):
        self.argv = sys.argv[1:]  # Store command-line arguments if needed
        self.scale = 1.0
        if "--skip-intro" in self.argv:
            self.state = State.MAIN_MENU
        else:
            self.state = State.INTRO
        self.seconds_since_start = 0.0
        self.mouse_down_primary_last_frame = False
        # Track keys that were down in the previous frame so we can detect
        # new key presses (edge detection).
        self.keys_down_last_frame = set()
        self._load_assets()
        self._initialize_intro()
        self._initialize_button_list_settings()
        self._load_data()
        self._initialize_new_game()
        self.game = None  # Will be initialized properly in State.NEW_GAME

    def _update_settings(self, from_game: bool):
        # Settings
        # TODO: implement actual settings options and functionality
        # Back button
        hover = is_point_in_rect(
            self.mouse_pos,
            V(self.screen_right.x, self.screen_bottom.y),
            V(
                self.screen_right.x - (130 * self.scale),
                self.screen_bottom.y + (40 * self.scale),
            ),
        )
        if hover:
            if self.mouse_pressed:
                if from_game:
                    self.state = State.PAUSED
                else:
                    self.state = State.MAIN_MENU

    def _update_load_game(self, from_game: bool):
        # Draw load game options
        # TODO: implement actual load game options and functionality
        # Back button
        hover = is_point_in_rect(
            self.mouse_pos,
            V(self.screen_right.x, self.screen_bottom.y),
            V(
                self.screen_right.x - (130 * self.scale),
                self.screen_bottom.y + (40 * self.scale),
            ),
        )
        if hover:
            if self.mouse_pressed:
                if from_game:
                    self.state = State.PAUSED
                else:
                    self.state = State.MAIN_MENU

    def _update_intro(self):
        self.intro_current_logo_time += self.deltatime
        num_logos = len(self.intro_logos)
        if self.intro_current_logo_index == 0:
            if self.intro_current_logo_time > self.intro_pre_delay:
                self.intro_current_logo_index = 1
                self.intro_current_logo_time = 0
                try:
                    if self.intro_boom_sound:
                        if "--disable-sound" not in self.argv:
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
                            if "--disable-sound" not in self.argv:
                                self.intro_boom_sound.play()
                    except Exception:
                        pass
        elif self.intro_current_logo_index == num_logos + 1:
            if self.intro_current_logo_time > self.intro_post_delay:
                self.state = State.MAIN_MENU

    def _update_credits(self):
        pass

    def _update_quit(self):
        quit()

    def _update_main_menu(self):
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
                self.screen_top.y
                - (
                    (
                        self.button_list_button_top_offset
                        + self.button_list_button_height / 2
                    )
                    + (
                        i
                        * (
                            self.button_list_button_height
                            + self.button_list_button_padding
                        )
                    )
                )
                * self.scale
            )
            width = self.button_list_button_width * self.scale
            height = self.button_list_button_height * self.scale
            ax = x - width / 2
            ay = y - height / 2
            bx = x + width / 2
            by = y + height / 2
            hover = is_point_in_rect(self.mouse_pos, V(ax, ay), V(bx, by))
            if hover and self.mouse_pressed:
                self.state = button

    def _update_new_game(self):
        # God list selection
        for i, god in enumerate(self.gods):
            hover = is_point_in_rect(
                self.mouse_pos,
                V(
                    self.screen_left.x + (1 * self.scale),
                    self.screen_top.y - (1 * self.scale) - (i * 25 * self.scale),
                ),
                V(
                    self.screen_left.x + (149 * self.scale),
                    self.screen_top.y
                    - (1 * self.scale)
                    - (i * 25 * self.scale)
                    - (25 * self.scale),
                ),
            )
            if hover and self.mouse_pressed:
                self.new_game_selected_god = i
        # Start button
        hover = is_point_in_rect(
            self.mouse_pos,
            V(self.screen_right.x, self.screen_bottom.y),
            V(
                self.screen_right.x - (130 * self.scale),
                self.screen_bottom.y + (40 * self.scale),
            ),
        )
        if hover:
            if self.mouse_pressed:
                self.game = Game(self.gods[self.new_game_selected_god])
                self.state = State.PLAYING

    def _update_load_game_menu(self):
        self._update_load_game(False)

    def _update_settings_menu(self):
        self._update_settings(False)

    def _update_playing(self):
        hover = (
            distance(
                self.mouse_pos,
                V(
                    self.screen_left.x + (15 * self.scale),
                    self.screen_bottom.y + (15 * self.scale),
                ),
            )
            < 10 * self.scale
        )
        if hover:
            if self.mouse_pressed:
                self.state = State.PAUSED
        # Keyboard-driven link selection: if we're on a screen with
        # lettered links (A, B, C, ...), allow pressing the corresponding
        # key to jump to the linked screen. We only react to a key when
        # it transitions from up -> down (edge detection) to avoid
        # repeated firings while the key is held.
        if self.game is not None:
            try:
                current_screen = self.game.god.tree.screens[
                    self.game.current_screen_index
                ]
            except Exception:
                current_screen = None
        else:
            current_screen = None
        if current_screen is not None and current_screen.links:
            # For each link map index 0->A, 1->B, etc.
            for i, link in enumerate(current_screen.links):
                if i >= 26:
                    break  # only map up to A to Z
                key_name = chr(ord("A") + i)
                try:
                    key_enum = Key[key_name]
                except Exception:
                    continue
                pressed_now = self.keydown(key_enum)
                was_pressed = key_enum in self.keys_down_last_frame
                # if newly pressed, follow the link
                if pressed_now and not was_pressed:
                    target_id = link.target
                    # find screen index by id
                    for idx, screen in enumerate(self.game.god.tree.screens):
                        if screen.id == target_id:
                            self.game.current_screen_index = idx
                            break

    def _update_paused(self):
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
                self.screen_top.y
                - (
                    (
                        self.button_list_button_top_offset
                        + self.button_list_button_height / 2
                    )
                    + (
                        i
                        * (
                            self.button_list_button_height
                            + self.button_list_button_padding
                        )
                    )
                )
                * self.scale
            )
            width = self.button_list_button_width * self.scale
            height = self.button_list_button_height * self.scale
            ax = x - width / 2
            ay = y - height / 2
            bx = x + width / 2
            by = y + height / 2
            hover = is_point_in_rect(self.mouse_pos, V(ax, ay), V(bx, by))
            if hover and self.mouse_pressed:
                self.state = button

    def _update_load_game_playing(self):
        self._update_load_game(True)

    def _update_settings_playing(self):
        self._update_settings(True)

    def update(self):
        self.mouse_pressed = (
            self.mouse_down_primary and not self.mouse_down_primary_last_frame
        )
        scale_x = self.width / self._original_width
        scale_y = self.height / self._original_height
        self.scale = (scale_x + scale_y) / 2.0
        self.seconds_since_start += self.deltatime
        if self.state == State.INTRO:
            self._update_intro()
        elif self.state == State.CREDITS:
            self._update_credits()
        elif self.state == State.QUIT:
            self._update_quit()
        elif self.state == State.MAIN_MENU:
            self._update_main_menu()
        elif self.state == State.NEW_GAME:
            self._update_new_game()
        elif self.state == State.LOAD_GAME_MENU:
            self._update_load_game_menu()
        elif self.state == State.SETTINGS_MENU:
            self._update_settings_menu()
        elif self.state == State.PLAYING:
            self._update_playing()
        elif self.state == State.PAUSED:
            self._update_paused()
        elif self.state == State.LOAD_GAME_PLAYING:
            self._update_load_game_playing()
        elif self.state == State.SETTINGS_PLAYING:
            self._update_settings_playing()
        else:
            raise Exception(f"Unknown state: {self.state} in update")
        self.mouse_down_primary_last_frame = self.mouse_down_primary
        # Update keys_down_last_frame for A to Z so the next frame can detect
        # edges. Keep only keys we care about (A to Z) to keep the set small.
        new_keys = set()
        for i in range(26):
            key_name = chr(ord("A") + i)
            try:
                key_enum = Key[key_name]
            except Exception:
                continue
            if self.keydown(key_enum):
                new_keys.add(key_enum)
        self.keys_down_last_frame = new_keys

    def _draw_settings(self, from_game: bool):
        # Draw background of play area only if from_game is true
        if from_game:
            if "--remove-transparency" not in self.argv:
                self._draw_playing()
                self.fill_rect(
                    self.screen_bottom_left, self.screen_top_right, Color(0, 0, 0, 150)
                )
        # Draw settings options
        # TODO: implement actual settings options and functionality
        # Draw back button
        hover = is_point_in_rect(
            self.mouse_pos,
            V(self.screen_right.x, self.screen_bottom.y),
            V(
                self.screen_right.x - (130 * self.scale),
                self.screen_bottom.y + (40 * self.scale),
            ),
        )
        self.fill_rounded_rect(
            V(self.screen_right.x, self.screen_bottom.y),
            V(
                self.screen_right.x - (130 * self.scale),
                self.screen_bottom.y + (40 * self.scale),
            ),
            Color(40, 40, 40) if hover else Color(30, 30, 30),
            int(2 * self.scale),
            Color(50, 50, 50),
            top_left_roundness=10 * self.scale,
            steps=10,
        )
        self.draw_text(
            "Back",
            V(
                self.screen_right.x - (65 * self.scale),
                self.screen_bottom.y + (20 * self.scale),
            ),
            self.main_font.new_size(int(30 * self.scale)),
            Color(255, 255, 255),
            Origin.CENTER,
        )

    def _draw_load_game(self, from_game: bool):
        # Draw background of play area only if from_game is true
        if from_game:
            if "--remove-transparency" not in self.argv:
                self._draw_playing()
                self.fill_rect(
                    self.screen_bottom_left, self.screen_top_right, Color(0, 0, 0, 150)
                )
        # Draw load game options
        # TODO: implement actual load game options and functionality
        # Draw back button
        hover = is_point_in_rect(
            self.mouse_pos,
            V(self.screen_right.x, self.screen_bottom.y),
            V(
                self.screen_right.x - (130 * self.scale),
                self.screen_bottom.y + (40 * self.scale),
            ),
        )
        self.fill_rounded_rect(
            V(self.screen_right.x, self.screen_bottom.y),
            V(
                self.screen_right.x - (130 * self.scale),
                self.screen_bottom.y + (40 * self.scale),
            ),
            Color(40, 40, 40) if hover else Color(30, 30, 30),
            int(2 * self.scale),
            Color(50, 50, 50),
            top_left_roundness=10 * self.scale,
            steps=10,
        )
        self.draw_text(
            "Back",
            V(
                self.screen_right.x - (65 * self.scale),
                self.screen_bottom.y + (20 * self.scale),
            ),
            self.main_font.new_size(int(30 * self.scale)),
            Color(255, 255, 255),
            Origin.CENTER,
        )

    def _draw_intro(self):
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
                    V(self.screen_center.x, self.screen_center.y),
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

    def _draw_credits(self):
        pass

    def _draw_quit(self):
        pass

    def _draw_main_menu(self):
        buttons = ["New Game", "Load Game", "Settings", "Credits", "Quit"]
        for i, button in enumerate(buttons):
            x = 0
            y = (
                self.screen_top.y
                - (
                    (
                        self.button_list_button_top_offset
                        + self.button_list_button_height / 2
                    )
                    + (
                        i
                        * (
                            self.button_list_button_height
                            + self.button_list_button_padding
                        )
                    )
                )
                * self.scale
            )
            width = self.button_list_button_width * self.scale
            height = self.button_list_button_height * self.scale
            ax = x - width / 2
            ay = y - height / 2
            bx = x + width / 2
            by = y + height / 2
            hover = is_point_in_rect(self.mouse_pos, V(ax, ay), V(bx, by))
            self.fill_rounded_rect(
                V(ax, ay),
                V(bx, by),
                (
                    self.button_list_button_hover_color
                    if hover
                    else self.button_list_button_color
                ),
                int(self.button_list_button_outline_thickness),
                self.button_list_button_outline_color,
                self.button_list_button_roundness * self.scale,
                self.button_list_button_roundness * self.scale,
                self.button_list_button_roundness * self.scale,
                self.button_list_button_roundness * self.scale,
                1,
            )
            self.draw_text(
                button,
                V(x, y),
                self.button_list_button_text_font,
                self.button_list_button_text_color,
                Origin.CENTER,
            )
        self.draw_text(
            "Fate of the Gods",
            V(
                self.screen_center.x,
                self.screen_top.y - (self.button_list_title_top_offset * self.scale),
            ),
            self.button_list_title_font,
            self.button_list_button_text_color,
            Origin.CENTER,
        )

    def _draw_new_game(self):
        # God list
        self.fill_rect(
            V(self.screen_left.x, self.screen_top.y),
            V(self.screen_left.x + (150 * self.scale), self.screen_bottom.y),
            Color(30, 30, 30),
            int(2 * self.scale),
            Color(50, 50, 50),
        )
        # God image
        self.fill_rect(
            V(self.screen_right.x, self.screen_top.y),
            V(
                self.screen_right.x - (130 * self.scale),
                self.screen_top.y - (150 * self.scale),
            ),
            Color(30, 30, 30),
            int(2 * self.scale),
            Color(50, 50, 50),
        )
        # God name and stats
        self.fill_rect(
            V(self.screen_left.x + (150 * self.scale), self.screen_top.y),
            V(
                self.screen_right.x - (130 * self.scale),
                self.screen_top.y - (150 * self.scale),
            ),
            Color(0, 0, 0),
        )
        # God lore
        self.fill_rect(
            V(
                self.screen_left.x + (150 * self.scale),
                self.screen_top.y - (150 * self.scale),
            ),
            V(self.screen_right.x, self.screen_bottom.y),
            Color(0, 0, 0),
        )
        # Gods list
        for i, god in enumerate(self.gods):
            hover = is_point_in_rect(
                self.mouse_pos,
                V(
                    self.screen_left.x + (1 * self.scale),
                    self.screen_top.y - (1 * self.scale) - (i * 25 * self.scale),
                ),
                V(
                    self.screen_left.x + (149 * self.scale),
                    self.screen_top.y
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
                    self.screen_left.x + (1 * self.scale),
                    self.screen_top.y - (1 * self.scale) - (i * 25 * self.scale),
                ),
                V(
                    self.screen_left.x + (149 * self.scale),
                    self.screen_top.y
                    - (1 * self.scale)
                    - (i * 25 * self.scale)
                    - (25 * self.scale),
                ),
                color,
            )
            self.draw_text(
                god.name,
                V(
                    self.screen_left.x + (55 * self.scale) - (3 * self.scale),
                    self.screen_top.y - (25 * self.scale * i) + (3 * self.scale),
                ),
                self.main_font.new_size(int(30 * self.scale)),
                Color(200, 255, 200),
                Origin.TOP_RIGHT,
            )
        # God image
        selected_god = self.gods[self.new_game_selected_god]
        try:
            self.draw_image(
                Image(
                    get_asset_path(
                        f"images/god/{selected_god.image}/{selected_god.image}.png"
                    )
                ),
                V(
                    self.screen_right.x - (65 * self.scale),
                    self.screen_top.y - (75 * self.scale),
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
                get_asset_path(
                    f'images/god/{
                        selected_god.image}/{
                        selected_god.image}.png')}")
        # God name
        self.draw_text(
            selected_god.name,
            V(
                self.screen_left.x + (155 * self.scale) + (3 * self.scale),
                self.screen_top.y + (5 * self.scale),
            ),
            self.heading_font.new_size(int(40 * self.scale)),
            Color(255, 255, 255),
            Origin.TOP_LEFT,
        )
        # God lore
        self.draw_text_word_wrap(
            selected_god.info,
            V(
                self.screen_left.x + (155 * self.scale) + (3 * self.scale),
                self.screen_top.y - (155 * self.scale) + (3 * self.scale),
            ),
            self.main_font.new_size(int(30 * self.scale)),
            Color(255, 255, 255),
            Origin.TOP_LEFT,
            wrap_distance=abs(
                self.screen_left.x
                - (self.screen_left.x + (155 * self.scale) + (3 * self.scale))
            )
            * 2,
        )
        # Start button
        hover = is_point_in_rect(
            self.mouse_pos,
            V(self.screen_right.x, self.screen_bottom.y),
            V(
                self.screen_right.x - (130 * self.scale),
                self.screen_bottom.y + (40 * self.scale),
            ),
        )
        self.fill_rounded_rect(
            V(self.screen_right.x, self.screen_bottom.y),
            V(
                self.screen_right.x - (130 * self.scale),
                self.screen_bottom.y + (40 * self.scale),
            ),
            Color(40, 40, 40) if hover else Color(30, 30, 30),
            int(2 * self.scale),
            Color(50, 50, 50),
            top_left_roundness=10 * self.scale,
            steps=10,
        )
        self.draw_text(
            "Start Game",
            V(
                self.screen_right.x - (65 * self.scale),
                self.screen_bottom.y + (20 * self.scale),
            ),
            self.main_font.new_size(int(30 * self.scale)),
            Color(255, 255, 255),
            Origin.CENTER,
        )

    def _draw_load_game_menu(self):
        self._draw_load_game(False)

    def _draw_settings_menu(self):
        self._draw_settings(False)

    def _draw_playing(self):
        # Context image
        self.draw_image(
            self.trees_scene,
            V(0 * self.scale, 110 * self.scale),
            origin=Origin.CENTER,
            scale_x=self.scale,
            scale_y=self.scale,
            antialiasing=False,
        )
        # Heading and main text come from the current screen (if available)
        if self.game is not None:
            try:
                current_screen = self.game.god.tree.screens[
                    self.game.current_screen_index
                ]
            except Exception:
                current_screen = None
        else:
            current_screen = None
        heading_text = (
            current_screen.title if current_screen is not None else "Heading text"
        )
        links = []
        for i, link in enumerate(current_screen.links):
            links.append(f"{"ABCDEFGHIJKLMNOPQRSTUVWXYZ"[i]}: {link.label}")
        links_text = "\n".join(links)
        main_text = (
            f"{current_screen.text}\nPress:\n{links_text}"
            if current_screen is not None
            else "Main text"
        )
        # Heading text (left area)
        self.draw_text(
            heading_text,
            V(-230 * self.scale, 40 * self.scale),
            font=self.heading_font.new_size(int(self.heading_font.size * self.scale)),
            color=Color(255, 255, 255),
            origin=Origin.TOP_LEFT,
        )
        # Main text (left area)
        self.draw_text_word_wrap(
            main_text,
            V(-230 * self.scale, 10 * self.scale),
            self.main_font.new_size(int(self.main_font.size * self.scale)),
            Color(255, 255, 255),
            Origin.TOP_LEFT,
            wrap_distance=abs(
                self.screen_right.x - (-230 * self.scale) + (-10 * self.scale)
            ),
        )
        # Pause button
        hover = (
            distance(
                self.mouse_pos,
                V(
                    self.screen_left.x + (15 * self.scale),
                    self.screen_bottom.y + (15 * self.scale),
                ),
            )
            < 10 * self.scale
        )
        self.fill_circle(
            V(
                self.screen_left.x + (15 * self.scale),
                self.screen_bottom.y + (15 * self.scale),
            ),
            10 * self.scale,
            Color(50, 50, 50) if hover else Color(40, 40, 40),
        )
        self.draw_text(
            "||",
            V(
                self.screen_left.x + (15 * self.scale),
                self.screen_bottom.y + (15 * self.scale),
            ),
            self.main_font.new_size(int(17 * self.scale)),
            Color(255, 255, 255),
            Origin.CENTER,
        )

    def _draw_paused(self):
        # Draw background of play area
        if "--remove-transparency" not in self.argv:
            self._draw_playing()
            self.fill_rect(
                self.screen_bottom_left, self.screen_top_right, Color(0, 0, 0, 150)
            )
        # Draw buttons
        buttons = ["Resume", "Load Game", "Save Game", "Settings", "Exit Game"]
        for i, button in enumerate(buttons):
            x = 0
            y = (
                self.screen_top.y
                - (
                    (
                        self.button_list_button_top_offset
                        + self.button_list_button_height / 2
                    )
                    + (
                        i
                        * (
                            self.button_list_button_height
                            + self.button_list_button_padding
                        )
                    )
                )
                * self.scale
            )
            width = self.button_list_button_width * self.scale
            height = self.button_list_button_height * self.scale
            ax = x - width / 2
            ay = y - height / 2
            bx = x + width / 2
            by = y + height / 2
            hover = is_point_in_rect(self.mouse_pos, V(ax, ay), V(bx, by))
            self.fill_rounded_rect(
                V(ax, ay),
                V(bx, by),
                (
                    self.button_list_button_hover_color
                    if hover
                    else self.button_list_button_color
                ),
                int(self.button_list_button_outline_thickness),
                self.button_list_button_outline_color,
                self.button_list_button_roundness * self.scale,
                self.button_list_button_roundness * self.scale,
                self.button_list_button_roundness * self.scale,
                self.button_list_button_roundness * self.scale,
                1,
            )
            self.draw_text(
                button,
                V(x, y),
                self.button_list_button_text_font,
                self.button_list_button_text_color,
                Origin.CENTER,
            )
        self.draw_text(
            "Paused",
            V(
                self.screen_center.x,
                self.screen_top.y - (self.button_list_title_top_offset * self.scale),
            ),
            self.button_list_title_font,
            self.button_list_button_text_color,
            Origin.CENTER,
        )

    def _draw_load_game_playing(self):
        self._draw_load_game(True)

    def _draw_settings_playing(self):
        self._draw_settings(True)

    def draw(self):
        self.clear(Color(0, 0, 0))
        if self.state == State.INTRO:
            self._draw_intro()
        elif self.state == State.CREDITS:
            self._draw_credits()
        elif self.state == State.QUIT:
            self._draw_quit()
        elif self.state == State.MAIN_MENU:
            self._draw_main_menu()
        elif self.state == State.NEW_GAME:
            self._draw_new_game()
        elif self.state == State.LOAD_GAME_MENU:
            self._draw_load_game_menu()
        elif self.state == State.SETTINGS_MENU:
            self._draw_settings_menu()
        elif self.state == State.PLAYING:
            self._draw_playing()
        elif self.state == State.PAUSED:
            self._draw_paused()
        elif self.state == State.LOAD_GAME_PLAYING:
            self._draw_load_game_playing()
        elif self.state == State.SETTINGS_PLAYING:
            self._draw_settings_playing()
        else:
            raise Exception(f"Unknown state: {self.state} in update")

    def on_quit(self):
        try:
            self.intro_boom_sound.stop()
        except Exception:
            pass


def main():
    App().start()


if __name__ == "__main__":
    main()
