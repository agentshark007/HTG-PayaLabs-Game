import logging
import logging.handlers
import math
import os
import sys
from enum import Enum

from colorlog import ColoredFormatter

from pgiud import *

data_directory = "data/"

log_format = "%(asctime)s [%(levelname)s]: %(message)s"
log_file = "game.log"
log_level = logging.DEBUG
console_handler = logging.StreamHandler(sys.stdout)
console_formatter = ColoredFormatter(
    "%(log_color)s%(asctime)s [%(levelname)s]: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    log_colors={
        "DEBUG": "cyan",
        "INFO": "green",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "bold_red",
    },
)
console_handler.setFormatter(console_formatter)
file_handler = logging.handlers.RotatingFileHandler(
    log_file, maxBytes=2 * 1024 * 1024, backupCount=3
)
file_handler.setFormatter(logging.Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S"))
logging.basicConfig(
    level=log_level, handlers=[console_handler, file_handler], force=True
)


def is_between(x, a, b):
    """Return True if x is between a and b (inclusive)."""
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
    """Return True if point is inside the rectangle defined by a and b."""
    return is_between(point.x, a.x, b.x) and is_between(point.y, a.y, b.y)


def split_nonempty_lines(text: str):
    """Split text into non-empty lines."""
    return [line for line in text.splitlines() if line.strip()]


def distance(a, b):
    """Calculate Euclidean distance between points a and b."""
    return math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def get_asset_path(path):
    """Return absolute path for asset given a relative path."""
    return str(os.path.join(BASE_DIR, "assets", path))


class State(Enum):
    """Game state enumeration."""

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
    """Represents a link/choice in a game screen tree."""

    def __init__(self, target, label):
        self.target = target
        self.label = label


class Screen:
    """Represents a screen in the game tree."""

    def __init__(self, encoded: str, screen_id: str = None):
        self.id = screen_id
        lines = split_nonempty_lines(encoded)
        links = []
        self.title = ""
        self.text = ""
        self.image = ""
        for line in lines:
            if line.startswith("title: "):
                self.title = line[len("title: ") :].strip()
            elif line.startswith("text: "):
                self.text = line[len("text: ") :].strip()
            elif line.startswith("image: "):
                self.image = line[len("image: ") :].strip()
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
    """Represents the decision tree for a god's story."""

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
    """Represents a god character loaded from data."""

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
    """Represents a game session for a selected god."""

    def __init__(self, god: God):
        self.god = god
        self.current_screen_index = god.start_screen_index


class App(Window):
    """
    Main application class for Fate of the Gods.
    Handles initialization, state management, asset loading, main loop, and rendering.
    Inherits from Window (pgiud).
    """

    def __init__(self):
        """Initialize the App window and game state."""
        super().__init__(
            width=480,
            height=360,
            title="Fate of the Gods",
            resizable=Resizable.ASPECT,
            origin=Origin.CENTER,
        )

    def set_state(self, new_state: State):
        """Set the current game state."""
        logging.info(f"State changed from {self.state} to {new_state}.")
        self.state = new_state

    def _find_arg_with_prefix(self, prefix):
        """Find command-line argument with given prefix."""
        result = next((s for s in self.argv if s.startswith(prefix)), None)
        return result

    def _parse_argv(self):
        """Parse command-line arguments."""
        self.argv = sys.argv[1:]

    def _parse_log_level(self):
        """Parse log level from command-line arguments."""
        level_arg = self._find_arg_with_prefix("--level=")
        if level_arg:
            result = level_arg.split("=", 1)[1]
            return result
        return None

    def _setup_state(self):
        """Set up initial game state based on arguments."""
        if "--skip-intro" in self.argv:
            self.state = State.MAIN_MENU
        else:
            self.state = State.INTRO
        self.seconds_since_start = 0.0
        self.mouse_down_primary_last_frame = False
        self.keys_down_last_frame = set()

    def initialize(self):
        """Initialize game assets, state, and data."""
        logging.debug("App.initialize() called.")
        self._parse_argv()
        log_level = self._parse_log_level()
        self._initialize_logging(log_level)
        logging.info("Initializing...")
        try:
            self.scale = 1.0
            self._setup_state()
            logging.debug("State setup complete.")
            self._load_assets()
            logging.debug("Assets loaded.")
            self._initialize_intro()
            logging.debug("Intro initialized.")
            self._initialize_button_list_settings()
            logging.debug("Button list settings initialized.")
            self._initialize_settings()
            logging.debug("Settings initialized.")
            self._load_data()
            logging.debug("Data loaded.")
            self._initialize_new_game()
            logging.debug("New game initialized.")
        except Exception:
            logging.error("Initialization failed with an error:", exc_info=True)
        finally:
            logging.info("Initialization complete.")

    def _initialize_logging(self, log_level=None):
        """Set up logging handlers and formatters."""

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

        logger = logging.getLogger()
        if log_level:
            try:
                logger.setLevel(decode_level(log_level))
            except Exception:
                logger.setLevel(logging.WARN)
        else:
            logger.setLevel(logging.WARN)

    def _load_assets(self):
        """Load game assets (images, sounds, fonts)."""
        logging.info("Loading assets...")
        try:
            logging.info("Loading scene images from 'images/scene'...")
            file_names = os.listdir(get_asset_path("images/scene"))
            self.scene_images = {}
            for file_name in file_names:
                logging.debug(f"Loading scene image: {file_name}")
                img_path = get_asset_path(os.path.join("images/scene", file_name))
                self.scene_images[os.path.splitext(file_name)[0]] = Image(img_path)
                logging.info(f"Loaded scene image: {file_name} from {img_path}")

            logging.info("Loading god images from 'images/god'...")
            file_names = os.listdir(get_asset_path("images/god"))
            self.god_images = {}
            for file_name in file_names:
                logging.debug(f"Loading god image: {file_name}")
                img_path = get_asset_path(os.path.join("images/god", file_name))
                self.god_images[os.path.splitext(file_name)[0]] = Image(img_path)
                logging.info(f"Loaded god image: {file_name} from {img_path}")

            logging.info("Loading fonts...")
            self.heading_font = Font(get_asset_path("fonts/Silkscreen-Regular.ttf"))
            self.main_font = Font(get_asset_path("fonts/VT323-Regular.ttf"))

            logging.info("Loading logos...")
            self.intro_payalabs_logo = Image(
                get_asset_path("images/intro/payalabs.png")
            )
            self.intro_pgiud_logo = Image(get_asset_path("images/intro/pgiud.png"))
            self.intro_pygame_logo = Image(get_asset_path("images/intro/pygame.png"))

            logging.info("Loading sound...")
            if "--disable-sound" not in self.argv:
                self.intro_boom_sound = Sound(get_asset_path("sounds/intro_boom.mp3"))

        except Exception:
            logging.error("Error loading assets:", exc_info=True)
        logging.info("Assets loaded.")

    def _load_data(self):
        """Load game data for gods from files."""
        logging.info("Loading god data from 'data/gods'...")
        gods_folder = get_asset_path("data/gods")
        self.gods_text = []
        god_files = []

        for name in os.listdir(gods_folder):
            path = os.path.join(gods_folder, name)
            if os.path.isfile(path) and name.lower().endswith(".txt"):
                logging.info(f"Loading god from file: {name}...")
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        self.gods_text.append(f.read())
                        god_files.append(name)
                    logging.info(f"God loaded from file: {name}.")
                except Exception:
                    logging.error(
                        f"Failed to load god from file: {name}", exc_info=True
                    )

        self.gods = []
        for i, god_text in enumerate(self.gods_text):
            try:
                self.gods.append(God(god_text))
                logging.info(f"Parsed god data for file: {
                    god_files[i] if i < len(god_files) else 'unknown'}.")
            except Exception as e:
                file_name = god_files[i] if i < len(god_files) else "unknown"
                logging.error(
                    f"Failed to parse god text from file '{file_name}': {e}",
                    exc_info=True,
                )
        logging.info("God data loaded.")

    def _initialize_intro(self):
        """Initialize intro screen assets and state."""
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
        """Initialize button list settings for menus."""
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

    def _initialize_settings(self):
        self.volume = 1
        self.potato_mode = False

    def _initialize_new_game(self):
        """Initialize new game selection state."""
        self.new_game_selected_god = None

    def _update_settings(self, from_game: bool):
        """Update settings menu state."""
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
                    self.set_state(State.PAUSED)
                else:
                    self.set_state(State.MAIN_MENU)

        # Delete all saves button
        hover = is_point_in_rect(
            self.mouse_pos,
            V(
                (self.width / -2) + (20 * self.scale),
                (self.height / 2) - (20 * self.scale),
            ),
            V(
                (self.width / -2) + (250 * self.scale),
                (self.height / 2) - (70 * self.scale),
            ),
        )
        if hover and self.mouse_pressed:
            folder_path = os.path.join(data_directory, "saves")
            for filename in os.listdir(folder_path):
                file_path = os.path.join(folder_path, filename)

                if os.path.isfile(file_path):
                    os.remove(file_path)

    def _update_load_game(self, from_game: bool):
        """Update load game menu state."""
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
                    self.set_state(State.PAUSED)
                else:
                    self.set_state(State.MAIN_MENU)

    def _update_intro(self):
        """Update intro screen state and handle logo transitions and sound."""
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
                self.set_state(State.MAIN_MENU)

    def _update_credits(self):
        """Update credits screen state."""
        pass

    def _update_quit(self):
        """Update quit screen state."""
        quit()

    def _update_main_menu(self):
        """Update main menu state and handle button selection."""
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
                self.set_state(button)
                if button == State.NEW_GAME:
                    self.new_game_selected_god = None

    def _update_new_game(self):
        """Update new game selection state."""
        for i, god in enumerate(self.gods):
            hover = is_point_in_rect(
                self.mouse_pos,
                V(
                    self.screen_left.x + (1 * self.scale),
                    self.screen_top.y
                    - (1 * self.scale)
                    - (i * 25 * self.scale)
                    - (30 * self.scale),
                ),
                V(
                    self.screen_left.x + (149 * self.scale),
                    self.screen_top.y
                    - (1 * self.scale)
                    - (i * 25 * self.scale)
                    - (25 * self.scale)
                    - (30 * self.scale),
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
        if hover and self.mouse_pressed and self.new_game_selected_god is not None:
            self.game = Game(self.gods[self.new_game_selected_god])
            self.set_state(State.PLAYING)

    def _update_load_game_menu(self):
        """Update load game menu state."""
        self._update_load_game(False)

    def _update_settings_menu(self):
        """Update settings menu state."""
        self._update_settings(False)

    def _update_playing(self):
        """Update playing state, handle user input and game progression."""
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
                self.set_state(State.PAUSED)
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
        """Update paused state."""
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
                self.set_state(button)

    def _update_load_game_playing(self):
        """Update load game while playing state."""
        self._update_load_game(True)

    def _update_settings_playing(self):
        """Update settings while playing state."""
        self._update_settings(True)

    def update(self):
        """Main update loop. Handles state transitions and input."""
        self.mouse_pressed = (
            self.mouse_down_primary and not self.mouse_down_primary_last_frame
        )
        scale_x = self.width / self._original_width
        scale_y = self.height / self._original_height
        self.scale = (scale_x + scale_y) / 2.0
        self.seconds_since_start += self.deltatime
        try:
            # State machine for game update
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
                raise Exception(f"Unknown state: {self.state}")
        except Exception:
            logging.error("Error during update:", exc_info=True)
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
        self.mouse_down_primary_last_frame = self.mouse_down_primary

    def _draw_settings(self, from_game: bool):
        """Draw settings menu."""
        if from_game:
            if "--remove-transparency" not in self.argv:
                # Draws the background overlay for settings
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
        # Draws the 'Back' button background
        self.fill_rounded_rect(
            V(self.screen_right.x, self.screen_bottom.y),
            V(
                self.screen_right.x - (130 * self.scale),
                self.screen_bottom.y + (40 * self.scale),
            ),
            Color(40, 40, 40) if hover else Color(30, 30, 30),
            int(1 * self.scale),
            Color(50, 50, 50),
            top_left_roundness=10 * self.scale,
            steps=10,
        )
        # Draws the 'Back' button label
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
        # Draw delete all saves button
        hover = is_point_in_rect(
            self.mouse_pos,
            V(
                (self.width / -2) + (20 * self.scale),
                (self.height / 2) - (20 * self.scale),
            ),
            V(
                (self.width / -2) + (250 * self.scale),
                (self.height / 2) - (70 * self.scale),
            ),
        )
        self.fill_rounded_rect(
            V(
                (self.width / -2) + (20 * self.scale),
                (self.height / 2) - (20 * self.scale),
            ),
            V(
                (self.width / -2) + (250 * self.scale),
                (self.height / 2) - (70 * self.scale),
            ),
            Color(40, 40, 40) if hover else Color(30, 30, 30),
            int(1 * self.scale),
            Color(50, 50, 50),
            top_left_roundness=int(5 * self.scale),
            top_right_roundness=int(5 * self.scale),
            bottom_left_roundness=int(5 * self.scale),
            bottom_right_roundness=int(5 * self.scale),
        )
        self.draw_text(
            "Delete All Saves",
            V(
                (self.width / -2) + (135 * self.scale),
                (self.height / 2) - (45 * self.scale),
            ),
            self.button_list_button_text_font.new_size(int(30 * self.scale)),
            Color(255, 255, 255),
            Origin.CENTER,
        )

    def _draw_load_game(self, from_game: bool):
        """Draw load game menu."""
        if from_game:
            if "--remove-transparency" not in self.argv:
                # Draws the background overlay for load game
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
        # Draws the 'Back' button background
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
        # Draws the 'Back' button label
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
        """Draw intro logos with fade-in/out effects."""
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
        """Draw credits screen."""
        pass

    def _draw_quit(self):
        """Draw quit screen."""
        pass

    def _draw_main_menu(self):
        """Draw main menu screen."""
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
            # Draws the main menu button background
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
            # Draws the main menu button label
            self.draw_text(
                button,
                V(x, y),
                self.button_list_button_text_font.new_size(
                    self.button_list_button_text_font.size * self.scale
                ),
                self.button_list_button_text_color,
                Origin.CENTER,
            )
        # Draws the main menu title
        self.draw_text(
            "Fate of the Gods",
            V(
                self.screen_center.x,
                self.screen_top.y - (self.button_list_title_top_offset * self.scale),
            ),
            self.button_list_title_font.new_size(
                self.button_list_title_font.size * self.scale
            ),
            self.button_list_button_text_color,
            Origin.CENTER,
        )

    def _draw_new_game(self):
        """Draw new game selection screen."""
        # Draws left panel background for god selection
        self.fill_rect(
            V(self.screen_left.x, self.screen_top.y),
            V(self.screen_left.x + (150 * self.scale), self.screen_bottom.y),
            Color(30, 30, 30),
            int(2 * self.scale),
            Color(50, 50, 50),
        )
        # Draws right panel background for god info
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
        # Draws center background for info
        self.fill_rect(
            V(self.screen_left.x + (150 * self.scale), self.screen_top.y),
            V(
                self.screen_right.x - (130 * self.scale),
                self.screen_top.y - (150 * self.scale),
            ),
            Color(0, 0, 0),
        )
        # Draws lower background for info
        self.fill_rect(
            V(
                self.screen_left.x + (150 * self.scale),
                self.screen_top.y - (150 * self.scale),
            ),
            V(self.screen_right.x, self.screen_bottom.y),
            Color(0, 0, 0),
        )
        # Draws the 'Select Your God' label
        self.draw_text(
            "Select Your God",
            V(
                self.screen_left.x + (75 * self.scale),
                self.screen_top.y - (15 * self.scale),
            ),
            self.main_font.new_size(int(23 * self.scale)),
            Color(255, 255, 255),
            Origin.CENTER,
        )
        for i, god in enumerate(self.gods):
            hover = is_point_in_rect(
                self.mouse_pos,
                V(
                    self.screen_left.x + (1 * self.scale),
                    self.screen_top.y
                    - (1 * self.scale)
                    - (i * 25 * self.scale)
                    - (30 * self.scale),
                ),
                V(
                    self.screen_left.x + (149 * self.scale),
                    self.screen_top.y
                    - (1 * self.scale)
                    - (i * 25 * self.scale)
                    - (25 * self.scale)
                    - (30 * self.scale),
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
            # Draws the god selection button background
            self.fill_rect(
                V(
                    self.screen_left.x + (1 * self.scale),
                    self.screen_top.y
                    - (1 * self.scale)
                    - (i * 25 * self.scale)
                    - (30 * self.scale),
                ),
                V(
                    self.screen_left.x + (149 * self.scale),
                    self.screen_top.y
                    - (1 * self.scale)
                    - (i * 25 * self.scale)
                    - (25 * self.scale)
                    - (30 * self.scale),
                ),
                color,
            )
            # Draws the god name label
            self.draw_text(
                god.name,
                V(
                    self.screen_left.x + (75 * self.scale),
                    self.screen_top.y - (25 * self.scale * i) - (30 * self.scale),
                ),
                self.main_font.new_size(int(23 * self.scale)),
                Color(200, 220, 200),
                Origin.TOP,
            )
        if self.new_game_selected_god is not None:
            selected_god = self.gods[self.new_game_selected_god]
            try:
                # Draws the selected god image
                self.draw_image(
                    self.god_images[selected_god.image],
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
            # Draws the selected god name label
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
            # Draws the selected god info text
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
        button_enabled = self.new_game_selected_god is not None
        button_color = (
            Color(40, 40, 40) if hover and button_enabled else Color(30, 30, 30)
        )
        if not button_enabled:
            button_color = Color(20, 20, 20)
        # Draws the 'Start Game' button background
        self.fill_rounded_rect(
            V(self.screen_right.x, self.screen_bottom.y),
            V(
                self.screen_right.x - (130 * self.scale),
                self.screen_bottom.y + (40 * self.scale),
            ),
            button_color,
            int(2 * self.scale),
            Color(50, 50, 50),
            top_left_roundness=10 * self.scale,
            steps=10,
        )
        # Draws the 'Start Game' button label
        self.draw_text(
            "Start Game",
            V(
                self.screen_right.x - (65 * self.scale),
                self.screen_bottom.y + (20 * self.scale),
            ),
            self.main_font.new_size(int(30 * self.scale)),
            Color(255, 255, 255) if button_enabled else Color(120, 120, 120),
            Origin.CENTER,
        )

    def _draw_load_game_menu(self):
        """Draw load game menu screen."""
        self._draw_load_game(False)

    def _draw_settings_menu(self):
        """Draw settings menu screen."""
        self._draw_settings(False)

    def _draw_playing(self):
        """Draw playing screen, including current story and choices."""
        # Draws the background scene image
        # Get the image name from the current screen
        image_name = self.game.god.tree.screens[self.game.current_screen_index].image
        scene_img = self.scene_images.get(image_name)
        if scene_img is None:
            if image_name:
                logging.warning(
                    f"Scene image '{image_name}' not found in scene_images. Using fallback."
                )
            else:
                logging.warning(
                    "No scene image specified for this screen. Using fallback."
                )
            scene_img = next(iter(self.scene_images.values()), None)
        if scene_img is not None:
            self.draw_image(
                scene_img,
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
        # Draws the heading text for the current screen
        self.draw_text(
            heading_text,
            V(-230 * self.scale, 40 * self.scale),
            font=self.heading_font.new_size(int(self.heading_font.size * self.scale)),
            color=Color(255, 255, 255),
            origin=Origin.TOP_LEFT,
        )
        # Draws the main story text and choices
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
        # Draws the pause button circle
        self.fill_circle(
            V(
                self.screen_left.x + (15 * self.scale),
                self.screen_bottom.y + (15 * self.scale),
            ),
            10 * self.scale,
            Color(50, 50, 50) if hover else Color(40, 40, 40),
        )
        # Draws the pause button label
        self.draw_line(
            V(
                (self.screen_left.x + (15 * self.scale)) + (-3 * self.scale),
                (self.screen_bottom.y + (15 * self.scale)) + (-5 * self.scale),
            ),
            V(
                (self.screen_left.x + (15 * self.scale)) + (-3 * self.scale),
                (self.screen_bottom.y + (15 * self.scale)) + (5 * self.scale),
            ),
            Color(255, 255, 255),
            int(2 * self.scale),
        )
        self.draw_line(
            V(
                (self.screen_left.x + (15 * self.scale)) + (3 * self.scale),
                (self.screen_bottom.y + (15 * self.scale)) + (-5 * self.scale),
            ),
            V(
                (self.screen_left.x + (15 * self.scale)) + (3 * self.scale),
                (self.screen_bottom.y + (15 * self.scale)) + (5 * self.scale),
            ),
            Color(255, 255, 255),
            int(2 * self.scale),
        )

    def _draw_paused(self):
        """Draw paused screen with overlay and buttons."""
        if "--remove-transparency" not in self.argv:
            # Draws the background overlay for paused state
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
            # Draws the paused menu button background
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
            # Draws the paused menu button label
            self.draw_text(
                button,
                V(x, y),
                self.button_list_button_text_font.new_size(
                    self.button_list_button_text_font.size * self.scale
                ),
                self.button_list_button_text_color,
                Origin.CENTER,
            )
        # Draws the 'Paused' title
        self.draw_text(
            "Paused",
            V(
                self.screen_center.x,
                self.screen_top.y - (self.button_list_title_top_offset * self.scale),
            ),
            self.button_list_title_font.new_size(
                self.button_list_title_font.size * self.scale
            ),
            self.button_list_button_text_color,
            Origin.CENTER,
        )

    def _draw_load_game_playing(self):
        """Draw load game while playing screen."""
        self._draw_load_game(True)

    def _draw_settings_playing(self):
        """Draw settings while playing screen."""
        self._draw_settings(True)

    def draw(self):
        """Main draw loop. Renders current state screen."""
        self.clear(Color(0, 0, 0))
        try:
            # State machine for drawing
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
                raise Exception(f"Unknown state: {self.state} in draw")
        except Exception:
            logging.error("Error during draw:", exc_info=True)

    def on_quit(self):
        """Handle application quit event."""
        if "--disable-sound" not in self.argv:
            try:
                self.intro_boom_sound.stop()
            except Exception:
                pass
        logging.info("Quitting application...")


def main():
    """Main entry point. Starts the application."""
    logging.info("Starting application from main entry point.")
    try:
        App().start()
        logging.info("Application exited normally.")
    except Exception as e:
        logging.exception("Unhandled exception in main entry point:")
        raise


if __name__ == "__main__":
    main()
