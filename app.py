import math
import os
import sys
from enum import Enum
import logging
from colorlog import ColoredFormatter



from pgiud import *


def is_between(x, a, b):
    """
    Check if x is between a and b (exclusive).
    Handles cases where a == b, a > b, and a < b.
    Args:
        x: Value to check.
        a: First bound.
        b: Second bound.
    Returns:
        bool: True if x is between a and b, False otherwise.
    """
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
    """
    Check if a point is inside the rectangle defined by points a and b.
    Args:
        point: Point to check (with x, y attributes).
        a: One corner of the rectangle.
        b: Opposite corner of the rectangle.
    Returns:
        bool: True if point is inside the rectangle, False otherwise.
    """
    return is_between(point.x, a.x, b.x) and is_between(point.y, a.y, b.y)


def split_nonempty_lines(text: str):
    """
    Split text into non-empty lines, stripping whitespace.
    Args:
        text (str): Input text.
    Returns:
        list: List of non-empty lines.
    """
    return [line for line in text.splitlines() if line.strip()]


def distance(a, b):
    """
    Calculate Euclidean distance between two points a and b.
    Args:
        a: First point (with x, y attributes).
        b: Second point (with x, y attributes).
    Returns:
        float: Distance between a and b.
    """
    return math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def get_asset_path(path):
    """
    Get the absolute path to an asset in the assets directory.
    Args:
        path (str): Relative path inside assets.
    Returns:
        str: Absolute path to the asset.
    """
    return str(os.path.join(BASE_DIR, "assets", path))


class State(Enum):
    """
    Enum representing the different states of the application/game.
    """

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
    """
    Represents a link/choice in a screen, pointing to another screen.
    """

    def __init__(self, target, label):
        self.target = target
        self.label = label


class Screen:
    """
    Represents a screen in the game tree, with title, text, and links.
    """

    def __init__(self, encoded: str, screen_id: str = None):
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
                if ": " in line:
                    target, _, link_text = line.partition(": ")
                    links.append(Link(target.strip(), link_text.strip()))
                else:
                    if self.text:
                        self.text += "\n" + line.strip()
                    else:
                        self.text = line.strip()
        self.links = links


class Tree:
    """
    Represents a tree of screens for a god/story.
    Parses encoded text to build the screen sequence.
    """

    def __init__(self, encoded):
        lines = split_nonempty_lines(encoded)
        screens = []
        ready = False
        screen_text = ""
        screen_id = None
        first_screen_index = None
        for line in lines:
            if line.startswith("#tree"):
                ready = True
                continue
            if not ready:
                continue
            if line.startswith("##"):
                if screen_id is not None:
                    screens.append(Screen(screen_text, screen_id))
                screen_id = line.removeprefix("##").strip()
                screen_text = ""
                if first_screen_index is None:
                    first_screen_index = len(screens)
            else:
                screen_text += line + "\n"
        if screen_id is not None and screen_text:
            screens.append(Screen(screen_text, screen_id))
        self.screens = screens
        self.first_screen_index = (
            first_screen_index if first_screen_index is not None else 0
        )


class God:
    """
    Represents a god in the game, with a tree of screens (story) and metadata.
    """

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
        self.start_screen_index = self.tree.first_screen_index


class Game:
    """
    Represents a game instance, with a god and the current screen index.
    """

    def __init__(self, god: God):
        self.god = god
        self.current_screen_index = god.start_screen_index


class App(Window):
    """
    Main application class, inheriting from Window.
    Manages states, updates, and draws for the game.
    """

    def __init__(self):
        super().__init__(
            width=480,
            height=360,
            title="Fate of the Gods",
            resizable=Resizable.ASPECT,
            origin=Origin.CENTER,
        )

    def _find_arg_with_prefix(self, prefix):
        """
        Returns the first argument in self.argv that starts with the given prefix, or None if not found.
        """
        return next((s for s in self.argv if s.startswith(prefix)), None)

    def _parse_argv(self):
        logging.info("Parsing command-line arguments.")
        self.argv = sys.argv[1:]

    def _parse_log_level(self):
        level_arg = self._find_arg_with_prefix("--level=")
        if level_arg:
            logging.info(f"Log level argument found: {level_arg}")
            return level_arg.split("=", 1)[1]
        logging.info("No log level argument found; using default.")
        return None

    def _setup_state(self):
        if "--skip-intro" in self.argv:
            logging.info("Skipping intro; setting state to MAIN_MENU.")
            self.state = State.MAIN_MENU
        else:
            logging.info("Showing intro; setting state to INTRO.")
            self.state = State.INTRO
        self.seconds_since_start = 0.0
        self.mouse_down_primary_last_frame = False
        self.keys_down_last_frame = set()

    def initialize(self):
        logging.info("App initialization started.")
        self._parse_argv()
        log_level = self._parse_log_level()
        self._initialize_logging(log_level)
        self.scale = 1.0
        self._setup_state()
        self._load_assets()
        self._initialize_intro()
        self._initialize_button_list_settings()
        self._load_data()
        self._initialize_new_game()
        logging.info("App initialization completed.")

    def _initialize_logging(self, log_level=None):
        logging.info(f"Initializing logging. Level: {log_level if log_level else 'WARN'}")
        def decode_level(level_str):
            level_str = level_str.upper()
            if level_str == "DEBUG":
                return logging.DEBUG
            elif level_str == "INFO":
                return logging.INFO
            elif level_str == "WARN":
                return logging.WARNING
            elif level_str == "ERROR":
                return logging.ERROR
            elif level_str == "CRITICAL":
                return logging.CRITICAL
            else:
                raise ValueError(f"Invalid log level: {level_str}")
        handler = logging.StreamHandler()
        formatter = ColoredFormatter(
            "%(log_color)s%(levelname)s: %(message)s",
            log_colors={
                'DEBUG':    'cyan',
                'INFO':     'green',
                'WARNING':  'yellow',
                'ERROR':    'red',
                'CRITICAL': 'bold_red',
            }
        )
        handler.setFormatter(formatter)
        logger = logging.getLogger()
        if log_level:
            try:
                logger.setLevel(decode_level(log_level))
            except Exception:
                logging.error(f"Invalid log level '{log_level}', defaulting to WARN.")
                logger.setLevel(logging.WARN)
        else:
            logger.setLevel(logging.WARN)
        logger.handlers = [handler]

    def _load_assets(self):
        logging.info("Loading game assets.")
        try:
            self.trees_scene = Image(get_asset_path("images/scene/trees.png"))
            self.heading_font = Font(get_asset_path("fonts/Silkscreen-Regular.ttf"))
            self.main_font = Font(get_asset_path("fonts/VT323-Regular.ttf"))
            self.intro_payalabs_logo = Image(get_asset_path("images/intro/payalabs.png"))
            self.intro_pgiud_logo = Image(get_asset_path("images/intro/pgiud.png"))
            self.intro_pygame_logo = Image(get_asset_path("images/intro/pygame.png"))
            if "--disable-sound" not in self.argv:
                self.intro_boom_sound = Sound(get_asset_path("sounds/intro_boom.mp3"))
            logging.info("Assets loaded successfully.")
        except Exception as e:
            logging.error(f"Error loading assets: {e}")

    def _load_data(self):
        logging.info("Loading game data (gods and stories).")
        gods_folder = get_asset_path("data/gods")
        self.gods_text = []
        for name in os.listdir(gods_folder):
            path = os.path.join(gods_folder, name)
            if os.path.isfile(path) and name.lower().endswith(".txt"):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        self.gods_text.append(f.read())
                    logging.info(f"Loaded god data: {name}")
                except Exception as e:
                    logging.error(f"Failed to load god data from {name}: {e}")
        self.gods = [God(i) for i in self.gods_text]
        logging.info(f"Total gods loaded: {len(self.gods)}")

    def _initialize_intro(self):
        logging.info("Initializing intro sequence.")
        self.intro_pre_delay = 1.5
        self.intro_logo_time = 1.0
        self.intro_post_delay = 2.0
        self.intro_current_logo_index = 0
        self.intro_current_logo_time = 0
        self.intro_logos = [
            self.intro_payalabs_logo,
            self.intro_pgiud_logo,
            self.intro_pygame_logo,
        ]

    def _initialize_button_list_settings(self):
        logging.info("Initializing button list settings.")
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
        logging.info("Initializing new game parameters.")
        self.new_game_selected_god = 0


    def _update_settings(self, from_game: bool):
        """
        Update logic for the settings menu, handling navigation and interactions.
        Args:
            from_game (bool): True if called from the game state, False otherwise.
        """
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
        """
        Update logic for the load game menu, handling navigation and interactions.
        Args:
            from_game (bool): True if called from the game state, False otherwise.
        """
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
        """
        Update logic for the intro sequence, handling logo display and transitions.
        """
        self.intro_current_logo_time += self.deltatime
        num_logos = len(self.intro_logos)
        if self.intro_current_logo_index == 0:
            if self.intro_current_logo_time > self.intro_pre_delay:
                self.intro_current_logo_index = 1
                self.intro_current_logo_time = 0
                if "--disable-sound" not in self.argv:
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
                    if "--disable-sound" not in self.argv:
                        try:
                            if self.intro_boom_sound:
                                self.intro_boom_sound.play()
                        except Exception:
                            pass
        elif self.intro_current_logo_index == num_logos + 1:
            if self.intro_current_logo_time > self.intro_post_delay:
                self.state = State.MAIN_MENU

    def _update_credits(self):
        """
        Update logic for the credits screen/menu.
        Currently, this does nothing, as the credits are static.
        """
        pass

    def _update_quit(self):
        """
        Update logic for quitting the game/application.
        """
        quit()

    def _update_main_menu(self):
        """
        Update logic for the main menu, handling button navigation and state changes.
        """
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
        """
        Update logic for selecting a new game, including god selection.
        """
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
        """
        Update logic for the load game menu when accessed from the main menu or paused state.
        """
        self._update_load_game(False)

    def _update_settings_menu(self):
        """
        Update logic for the settings menu when accessed from the main menu or paused state.
        """
        self._update_settings(False)

    def _update_playing(self):
        """
        Update logic for the playing state, including handling user input for navigation
        and interacting with the game world.
        """
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
            for i, link in enumerate(current_screen.links):
                if i >= 26:
                    break
                key_name = chr(ord("A") + i)
                try:
                    key_enum = Key[key_name]
                except Exception:
                    continue
                pressed_now = self.keydown(key_enum)
                was_pressed = key_enum in self.keys_down_last_frame
                if pressed_now and not was_pressed:
                    target_id = link.target
                    for idx, screen in enumerate(self.game.god.tree.screens):
                        if screen.id == target_id:
                            self.game.current_screen_index = idx
                            break

    def _update_paused(self):
        """
        Update logic for the paused state, including showing the pause menu and handling
        user input to resume or exit.
        """
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
        """
        Update logic for the load game menu when accessed from the playing state.
        """
        self._update_load_game(True)

    def _update_settings_playing(self):
        """
        Update logic for the settings menu when accessed from the playing state.
        """
        self._update_settings(True)

    def update(self):
        """
        Main update method, called every frame.
        Updates the application state, handles user input, and triggers state-specific updates.
        """
        prev_state = getattr(self, 'state', None)
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
            logging.error(f"Unknown state: {self.state} in update")
            raise Exception(f"Unknown state: {self.state} in update")
        if prev_state != self.state:
            logging.info(f"State changed: {prev_state} -> {self.state}")
        self.mouse_down_primary_last_frame = self.mouse_down_primary
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
        """
        Draw the settings menu.
        Args:
            from_game (bool): True if called from the game state, False otherwise.
        """
        if from_game:
            if "--remove-transparency" not in self.argv:
                self._draw_playing()
                self.fill_rect(
                    self.screen_bottom_left, self.screen_top_right, Color(0, 0, 0, 150)
                )
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
        """
        Draw the load game menu.
        Args:
            from_game (bool): True if called from the game state, False otherwise.
        """
        if from_game:
            if "--remove-transparency" not in self.argv:
                self._draw_playing()
                self.fill_rect(
                    self.screen_bottom_left, self.screen_top_right, Color(0, 0, 0, 150)
                )
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
        """
        Draw the intro sequence, showing logos with fade in/out effects.
        """
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
            pass

    def _draw_credits(self):
        """
        Draw the credits screen/menu.
        Currently, this does nothing, as the credits are static.
        """
        pass

    def _draw_quit(self):
        """
        Draw the quit confirmation screen/menu.
        """
        pass

    def _draw_main_menu(self):
        """
        Draw the main menu, including buttons for starting a new game,
        loading a game, settings, credits, and quitting.
        """
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
        """
        Draw the new game screen, including god selection and start game button.
        """
        self.fill_rect(
            V(self.screen_left.x, self.screen_top.y),
            V(self.screen_left.x + (150 * self.scale), self.screen_bottom.y),
            Color(30, 30, 30),
            int(2 * self.scale),
            Color(50, 50, 50),
        )
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
        self.fill_rect(
            V(self.screen_left.x + (150 * self.scale), self.screen_top.y),
            V(
                self.screen_right.x - (130 * self.scale),
                self.screen_top.y - (150 * self.scale),
            ),
            Color(0, 0, 0),
        )
        self.fill_rect(
            V(
                self.screen_left.x + (150 * self.scale),
                self.screen_top.y - (150 * self.scale),
            ),
            V(self.screen_right.x, self.screen_bottom.y),
            Color(0, 0, 0),
        )
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
        """
        Draw the load game menu when accessed from the main menu or paused state.
        """
        self._draw_load_game(False)

    def _draw_settings_menu(self):
        """
        Draw the settings menu when accessed from the main menu or paused state.
        """
        self._draw_settings(False)

    def _draw_playing(self):
        """
        Draw the playing state, including the game world and UI elements.
        """
        self.draw_image(
            self.trees_scene,
            V(0 * self.scale, 110 * self.scale),
            origin=Origin.CENTER,
            scale_x=self.scale,
            scale_y=self.scale,
            antialiasing=False,
        )
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
            links.append(f"{'ABCDEFGHIJKLMNOPQRSTUVWXYZ'[i]}: {link.label}")
        links_text = "\n".join(links)
        main_text = (
            f"{current_screen.text}\nPress:\n{links_text}"
            if current_screen is not None
            else "Main text"
        )
        self.draw_text(
            heading_text,
            V(-230 * self.scale, 40 * self.scale),
            font=self.heading_font.new_size(int(self.heading_font.size * self.scale)),
            color=Color(255, 255, 255),
            origin=Origin.TOP_LEFT,
        )
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
        """
        Draw the pause menu, allowing the player to resume, load, save, or change settings.
        """
        if "--remove-transparency" not in self.argv:
            self._draw_playing()
            self.fill_rect(
                self.screen_bottom_left, self.screen_top_right, Color(0, 0, 0, 150)
            )
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
        """
        Draw the load game menu when accessed from the playing state.
        """
        self._draw_load_game(True)

    def _draw_settings_playing(self):
        """
        Draw the settings menu when accessed from the playing state.
        """
        self._draw_settings(True)

    def draw(self):
        """
        Main draw method, called every frame.
        Clears the screen and calls the appropriate draw method based on the current state.
        """
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
        """
        Cleanup actions on quitting the application, like stopping sounds.
        """
        if "--disable-sound" not in self.argv:
            try:
                self.intro_boom_sound.stop()
            except Exception:
                pass


def main():
    App().start()


if __name__ == "__main__":
    main()
