import math
import os
import random
import shutil
import string
import sys
from enum import Enum
from typing import Optional

from pgiud import *


def is_between(x, a, b):
    """
    Check if a value is strictly between two bounds (exclusive), or equal if all are the same.
    Works correctly regardless of whether a > b or a < b.
    Args:
        x: The value to check
        a: First bound
        b: Second bound
    Returns:
        True if x is between a and b, or equal if a == b == x
    """
    if a == b:
        # Special case: all values are equal
        return x == a
    elif a > b:
        # A is greater than B
        return b < x < a
    elif a < b:
        # A is less than B
        return a < x < b
    else:
        return False


def is_point_in_rect(point, a, b):
    """
    Check if a point is inside a rectangle defined by two corners.
    Args:
        point: A point object with x and y attributes
        a: First corner of the rectangle
        b: Second corner of the rectangle (can be diagonal)
    Returns:
        True if the point is inside the rectangle
    """
    return is_between(point.x, a.x, b.x) and is_between(point.y, a.y, b.y)


def split_nonempty_lines(text: str):
    """
    Split text into non-empty lines with whitespace stripped.
    Args:
        text: Input text to split
    Returns:
        List of non-empty, stripped lines
    """
    return [line for line in text.splitlines() if line.strip()]


def distance(a, b):
    """
    Calculate the Euclidean distance between two points.
    Args:
        a: First point (must have x and y attributes)
        b: Second point (must have x and y attributes)
    Returns:
        Euclidean distance between the two points
    """
    return math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def get_absolute_path(path):
    """
    Get the absolute file path to an asset file.
    Args:
        path: Relative path within the assets directory (e.g., "assets/images/god/ares.png")
    Returns:
        Absolute path to the asset file
    """
    return str(os.path.join(BASE_DIR, path))


data_directory = get_absolute_path("data/")


class State(Enum):
    """
    Enumeration of all possible application and game states.
    Controls the flow between different screens and game modes.
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
    Represents a navigational link between scenes in the game story tree.
    Players can click on links to navigate to different story branches.
    """

    def __init__(self, target, label):
        self.target = target
        self.label = label


class Scene:
    """
    Represents a single scene/node in the game's story tree.
    Each scene contains text content, an optional background image, and links to other scenes.
    Format (text):
        text: "The scene narrative content"
        image: "image_name_without_extension"
        target_scene_id: "Link label text"
    """

    def __init__(self, encoded: str, scene_id: str = None):
        self.id = scene_id
        lines = split_nonempty_lines(encoded)
        links = []
        self.text = ""
        self.image = ""
        # Parse each line for scene attributes or links
        for line in lines:
            if line.startswith("text: "):
                self.text = line[len("text: ") :].strip()
            elif line.startswith("image: "):
                self.image = line[len("image: ") :].strip()
            else:
                if ": " in line:
                    # Parse link: "target: label"
                    target, _, link_text = line.partition(": ")
                    links.append(Link(target.strip(), link_text.strip()))
                else:
                    # Additional text lines
                    if self.text:
                        self.text += "\n" + line.strip()
                    else:
                        self.text = line.strip()
        self.links = links


class Tree:
    """
    Represents the complete story tree for a god character.
    Parses a structured text format containing multiple scenes and organizes them sequentially.
    """

    def __init__(self, encoded):
        lines = split_nonempty_lines(encoded)
        scenes = []
        ready = False
        scene_text = ""
        scene_id = None
        first_scene_index = None
        # Parse the tree structure from encoded text (marked by #tree header)
        for line in lines:
            if line.startswith("#tree"):
                ready = True
                continue
            if not ready:
                continue
            if line.startswith("##"):
                # New scene node (## marks scene boundaries)
                if scene_id is not None:
                    scenes.append(Scene(scene_text, scene_id))
                scene_id = line.removeprefix("##").strip()
                scene_text = ""
                if first_scene_index is None:
                    first_scene_index = len(scenes)
            else:
                scene_text += line + "\n"
        if scene_id is not None and scene_text:
            scenes.append(Scene(scene_text, scene_id))
        self.scenes = scenes
        # Index of the first scene in the tree (starting point for the story)
        self.first_scene_index = (
            first_scene_index if first_scene_index is not None else 0
        )


class God:
    """
    Represents a selectable god character with their biographical information and story.
    Each god has a name, description, portrait image, and a complete story tree.
    """

    def __init__(self, encoded: str):
        self.name: str = ""
        self.info: str = ""
        self.image: str = ""
        lines = split_nonempty_lines(encoded)
        # Parse god attributes from encoded text (before #tree marker)
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
        self.start_scene_index = self.tree.first_scene_index


class Game:
    """
    Represents an active game session for a selected god.
    Tracks the current scene within the god's story tree during gameplay.
    """

    def __init__(self, god: God):
        self.god = god
        self.current_scene_index = god.start_scene_index


class App(Window):
    """
    Main application class for "Fate of the Gods" interactive fiction game.
    Inherits from Window to manage game rendering, input, and state transitions.
    Coordinates all game systems including story progression, UI, audio, and saves.
    """

    def __init__(self):
        super().__init__(
            width=480,
            height=360,
            title="Fate of the Gods",
            resizable=Resizable.ASPECT,
            origin=Origin.CENTER,
        )

    def set_state(self, new_state: State):
        """
        Change the application state and log the transition.
        """
        self.state = new_state

    def _find_arg_with_prefix(self, prefix):
        """
        Find the first command-line argument with the given prefix.
        """
        result = next((s for s in self.argv if s.startswith(prefix)), None)
        return result

    def _parse_argv(self):
        """
        Parse command-line arguments (excluding script name).
        """
        self.argv = sys.argv[1:]

    def _parse_log_level(self):
        """
        Parse log level from command-line arguments.
        """
        level_arg = self._find_arg_with_prefix("--level=")
        if level_arg:
            result = level_arg.split("=", 1)[1]
            return result
        return None

    def _initialize_saving(self):
        """
        Ensure data_directory has exactly a saves folder and settings.txt file.
        If structure is missing or has extras, reset the directory and restore defaults.
        """
        expected_entries = {"saves", "settings.txt"}
        data_dir_exists = os.path.isdir(data_directory)
        current_entries = set(os.listdir(data_directory)) if data_dir_exists else set()
        valid_structure = (
            data_dir_exists
            and current_entries == expected_entries
            and os.path.isdir(os.path.join(data_directory, "saves"))
            and os.path.isfile(os.path.join(data_directory, "settings.txt"))
        )
        if valid_structure:
            return
        os.makedirs(data_directory, exist_ok=True)
        for name in os.listdir(data_directory):
            path = os.path.join(data_directory, name)
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
        os.makedirs(os.path.join(data_directory, "saves"), exist_ok=True)
        default_settings_path = get_absolute_path("assets/default_settings.txt")
        settings_path = os.path.join(data_directory, "settings.txt")
        with open(default_settings_path, "r", encoding="utf-8") as src, open(
            settings_path, "w", encoding="utf-8"
        ) as dst:
            dst.write(src.read())

    def _setup_state(self):
        """
        Set initial state based on command-line arguments.
        """
        if "--skip-intro" in self.argv:
            self.state = State.MAIN_MENU
        else:
            self.state = State.INTRO
        self.seconds_since_start = 0.0
        self.mouse_down_primary_last_frame = False
        self.keys_down_last_frame = set()

    def initialize(self):
        """
        Main initialization routine for the application. Loads assets, data, and sets up state.
        """
        self._parse_argv()
        try:
            self.scale = 1.0
            self._initialize_saving()
            self._setup_state()
            self._load_assets()
            self._initialize_intro()
            self._initialize_button_list_settings()
            self._initialize_settings()
            self._load_data()
            self._initialize_new_game()
        except Exception:
            raise
        finally:
            pass

    def _initialize_logging(self, log_level=None):
        """
        Placeholder for custom logging setup if needed.
        """
        pass

    def _load_assets(self):
        """
        Load all required game assets: images, fonts, and sounds.
        Assets are organized into directories for scenes, gods, fonts, and audio.
        """
        try:
            # Load scene background images
            file_names = os.listdir(get_absolute_path("assets/images/scene"))
            self.scene_images = {}
            for file_name in file_names:
                img_path = get_absolute_path(
                    os.path.join("assets/images/scene", file_name)
                )
                self.scene_images[os.path.splitext(file_name)[0]] = Image(img_path)
            # Load god character portrait images
            file_names = os.listdir(get_absolute_path("assets/images/god"))
            self.god_images = {}
            for file_name in file_names:
                img_path = get_absolute_path(
                    os.path.join("assets/images/god", file_name)
                )
                self.god_images[os.path.splitext(file_name)[0]] = Image(img_path)
            # Load fonts for UI text rendering
            self.heading_font = Font(
                get_absolute_path("assets/fonts/Silkscreen-Regular.ttf")
            )
            self.main_font = Font(get_absolute_path("assets/fonts/VT323-Regular.ttf"))
            # Load intro sequence logos
            self.intro_payalabs_logo = Image(
                get_absolute_path("assets/images/intro/payalabs.png")
            )
            self.intro_pgiud_logo = Image(
                get_absolute_path("assets/images/intro/pgiud.png")
            )
            self.intro_pygame_logo = Image(
                get_absolute_path("assets/images/intro/pygame.png")
            )
            # Load intro sequence sound effect (can be disabled via
            # --disable-sound)
            if "--disable-sound" not in self.argv:
                self.intro_boom_sound = Sound(
                    get_absolute_path("assets/sounds/intro_boom.mp3")
                )
        except Exception:
            raise

    def _load_data(self):
        """
        Load god character data from text files in the assets/data/gods directory.
        Parses god metadata and story trees for all available characters.
        """
        gods_folder = get_absolute_path("assets/data/gods")
        self.gods_text: list[str] = []
        god_files: list[str] = []
        # Read all god .txt files from the data directory
        for name in os.listdir(gods_folder):
            path = os.path.join(gods_folder, name)
            if os.path.isfile(path) and name.lower().endswith(".txt"):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        self.gods_text.append(f.read())
                        god_files.append(name)
                except Exception:
                    continue
        # Parse god objects from loaded text
        self.gods: list[God] = []
        for i, god_text in enumerate(self.gods_text):
            try:
                self.gods.append(God(god_text))
            except Exception:
                continue

    def _initialize_intro(self):
        """
        Set up intro logo sequence timing and images.
        Configures the sequence of logos displayed at game startup.
        """
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
        """
        Initialize UI layout and style settings for button lists used in menus.
        Configures button positioning, colors, fonts, and visual styling.
        """
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
        """
        Initialize default settings for volume and graphics mode.
        These settings can be modified through the settings menu.
        """
        self.volume = 1
        self.potato_mode = False

    def _initialize_new_game(self):
        """
        Initialize tracking for new game state.
        Tracks which god the player has selected for a new playthrough.
        """
        self.new_game_selected_god: Optional[int] = None
        self.game: Optional[Game] = None

    def _parse_weighted_targets(self, raw_target: str):
        """
        Parse target lists like "b3, b4*2, b5" into [("b3", 1.0), ("b4", 2.0), ("b5", 1.0)].
        """
        parsed_targets = []
        for token in raw_target.split(","):
            option = token.strip()
            if not option:
                continue
            target_id = option
            weight = 1.0
            # Weight syntax: target_id*weight (e.g. b4*3)
            if "*" in option:
                target_part, weight_part = option.rsplit("*", 1)
                target_id = target_part.strip()
                try:
                    weight = float(weight_part.strip())
                except ValueError:
                    continue
            if not target_id:
                continue
            if weight <= 0:
                continue
            parsed_targets.append((target_id, weight))
        return parsed_targets

    def _choose_target_id(self, raw_target: str):
        weighted_targets = self._parse_weighted_targets(raw_target)
        if not weighted_targets:
            return None
        target_ids = [target_id for target_id, _ in weighted_targets]
        weights = [weight for _, weight in weighted_targets]
        return random.choices(target_ids, weights=weights, k=1)[0]

    def _update_settings(self, from_game: bool):
        """
        Handle updates for the settings menu or in-game settings overlay.
        Manages settings button interactions and save file clearing.
        Args:
            from_game: True if called during gameplay (overlay), False from main menu
        """
        # Check if mouse is over the settings button (bottom right corner)
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
                # Return to previous state
                if from_game:
                    self.set_state(State.PAUSED)
                else:
                    self.set_state(State.MAIN_MENU)

    def _update_load_game(self, from_game: bool):
        """
        Handle updates for the load game menu or in-game load overlay.
        Manages navigation and returning to previous state.
        Args:
            from_game: True if called during gameplay (overlay), False from main menu
        """
        # Check if mouse is over the back/return button (bottom right corner)
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
                # Return to previous state
                if from_game:
                    self.set_state(State.PAUSED)
                else:
                    self.set_state(State.MAIN_MENU)

    def _update_intro(self):
        """
        Handle the intro logo sequence and transitions to the main menu.
        Manages timing for showing each logo with delays and sound effects.
        """
        self.intro_current_logo_time += self.deltatime
        num_logos = len(self.intro_logos)
        if self.intro_current_logo_index == 0:
            # Wait for pre-delay, then show first logo and play sound
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
            # Show each logo for a set time, then advance and play sound
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
            # After last logo, wait for post-delay then transition to main menu
            if self.intro_current_logo_time > self.intro_post_delay:
                self.set_state(State.MAIN_MENU)

    def _update_credits(self):
        """
        Handle updates for the credits scene.
        Currently, a placeholder for future credits implementation.
        """
        pass

    def _update_quit(self):
        """
        Handle the quit action and close the application.
        """
        quit()

    def _update_main_menu(self):
        """
        Handle updates for the main menu, including button hover and click logic.
        Displays the main menu with navigation buttons for different game states.
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
            # Calculate y position for each button in the menu (vertical
            # layout)
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
            # Check if mouse is over this button
            hover = is_point_in_rect(self.mouse_pos, V(ax, ay), V(bx, by))
            if hover and self.mouse_pressed:
                self.set_state(button)
                if button == State.NEW_GAME:
                    self.new_game_selected_god = None

    def _update_new_game(self):
        """
        Handle updates for the new game scene, including god selection and game start.
        Displays available gods and allows the player to select one and begin gameplay.
        """
        for i, god in enumerate(self.gods):
            # Calculate bounding box for each god selection button
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
        # Check if mouse is over the "start game" button (bottom right)
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
        """
        Handle updates for the load game menu.
        Wrapper method that calls the common load game handler for non-gameplay context.
        """
        self._update_load_game(False)

    def _update_settings_menu(self):
        """
        Handle updates for the settings menu.
        Wrapper method that calls the common settings handler for non-gameplay context.
        """
        self._update_settings(False)

    def _update_playing(self):
        """
        Handle updates for the main gameplay state.
        Manages pause button detection and clickable story links for scene navigation.
        """
        # Check if mouse is over the pause button (bottom left corner)
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
        # Get the current scene for the selected god
        current_game: Optional[Game] = self.game
        if current_game is None:
            return
        try:
            current_scene: Optional[Scene] = current_game.god.tree.scenes[
                current_game.current_scene_index
            ]
        except Exception:
            current_scene = None
        # Handle clickable links on the current scene (keys A-Z trigger links)
        if current_scene is not None and current_scene.links:
            for i, link in enumerate(current_scene.links):
                if i >= 26:
                    break
                # Map link index to keyboard key (A=0, B=1, etc.)
                key_name = chr(ord("A") + i)
                try:
                    key_enum = Key[key_name]
                except Exception:
                    continue
                pressed_now = self.keydown(key_enum)
                was_pressed = key_enum in self.keys_down_last_frame
                # Detect key press (pressed now but not last frame)
                if pressed_now and not was_pressed:
                    target_id = self._choose_target_id(link.target)
                    if target_id is None:
                        continue
                    # Find the target scene in the tree
                    found_target = False
                    for idx, scene in enumerate(current_game.god.tree.scenes):
                        if scene.id == target_id:
                            current_game.current_scene_index = idx
                            found_target = True
                            break
                    if not found_target:
                        pass

    def _update_paused(self):
        """
        Handle updates for the paused state.
        Displays pause menu with options to resume, load, adjust settings, or return to main menu.
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
            # Calculate y position for each pause menu button (vertical layout)
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
            # Check if mouse is over this button
            hover = is_point_in_rect(self.mouse_pos, V(ax, ay), V(bx, by))
            if hover and self.mouse_pressed:
                self.set_state(button)

    def _update_load_game_playing(self):
        # Handles updates for the in-game load game overlay
        self._update_load_game(True)

    def _update_settings_playing(self):
        # Handles updates for the in-game settings overlay
        self._update_settings(True)

    def update(self):
        """
        Main update routine called every frame.
        Handles state transitions, input processing, and scale calculations.
        Coordinates all game logic via state machine dispatch.
        """
        # Detect mouse click (primary button pressed this frame)
        self.mouse_pressed = (
            self.mouse_down_primary and not self.mouse_down_primary_last_frame
        )
        # Update scale based on window size changes
        scale_x = self.width / self._original_width
        scale_y = self.height / self._original_height
        self.scale = (scale_x + scale_y) / 2.0
        self.seconds_since_start += self.deltatime
        try:
            # State machine: call update method for current state
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
            pass
        # Track which keys are currently pressed (A-Z) for next frame
        # comparison
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
        # Draw the settings overlay/menu
        if from_game:
            if "--remove-transparency" not in self.argv:
                # Draw gameplay scene faded out behind settings
                self._draw_playing()
                self.fill_rect(
                    self.screen_bottom_left, self.screen_top_right, Color(0, 0, 0, 150)
                )
        # Draw the "Back" button (bottom right)
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
            int(1 * self.scale),
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
        # Draw the load game overlay/menu
        if from_game:
            if "--remove-transparency" not in self.argv:
                # Draw gameplay scene faded out behind load game overlay
                self._draw_playing()
                self.fill_rect(
                    self.screen_bottom_left, self.screen_top_right, Color(0, 0, 0, 150)
                )
        # Draw the "Back" button (bottom right)
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
        # Draw the intro logo sequence with fade-in and fade-out effects
        num_logos = len(self.intro_logos)
        idx = self.intro_current_logo_index
        if 1 <= idx <= num_logos:
            img = self.intro_logos[idx - 1]
            total = self.intro_logo_time
            t = self.intro_current_logo_time
            fade = min(0.3, total / 2.0)
            # Calculate alpha for fade-in/out
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

    def _draw_credits(self):
        # Draw the credits scene (currently a placeholder)
        pass

    def _draw_quit(self):
        # Draw the quit scene (currently a placeholder)
        pass

    def _draw_main_menu(self):
        # Draw the main menu with buttons for each major action
        buttons = ["New Game", "Load Game", "Settings", "Credits", "Quit"]
        for i, button in enumerate(buttons):
            x = 0
            # Calculate y position for each button
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
            # Draw button background and outline
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
            # Draw button label
            self.draw_text(
                button,
                V(x, y),
                self.button_list_button_text_font.new_size(
                    self.button_list_button_text_font.size * self.scale
                ),
                self.button_list_button_text_color,
                Origin.CENTER,
            )
        # Draw the game title at the center top
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
        # Draw the new game scene, including god selection list, god info, and the start button
        # Draw left panel for god selection
        self.fill_rect(
            V(self.screen_left.x, self.screen_top.y),
            V(self.screen_left.x + (150 * self.scale), self.screen_bottom.y),
            Color(30, 30, 30),
            int(2 * self.scale),
            Color(50, 50, 50),
        )
        # Draw right panel for god image/info
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
        # Draw center panel for god info
        self.fill_rect(
            V(self.screen_left.x + (150 * self.scale), self.screen_top.y),
            V(
                self.screen_right.x - (130 * self.scale),
                self.screen_top.y - (150 * self.scale),
            ),
            Color(0, 0, 0),
        )
        # Draw lower panel for god info
        self.fill_rect(
            V(
                self.screen_left.x + (150 * self.scale),
                self.screen_top.y - (150 * self.scale),
            ),
            V(self.screen_right.x, self.screen_bottom.y),
            Color(0, 0, 0),
        )
        # Draw title
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
        # Draw god selection buttons
        for i, god in enumerate(self.gods):
            # Calculate bounding box for each god selection
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
            # Highlight selection/hover
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
            # Draw god name
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
        # Draw selected god info and image
        if self.new_game_selected_god is not None:
            selected_god: God = self.gods[self.new_game_selected_god]
            try:
                # Draw god image with animation
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
                    get_absolute_path(
                        f'assets/images/god/{
                            selected_god.image}/{
                            selected_god.image}.png')}")
            # Draw god name
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
            # Draw god info (word-wrapped)
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
        # Draw the "Start" button (bottom right)
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
        self._draw_load_game(False)

    def _draw_settings_menu(self):
        self._draw_settings(False)

    def _draw_playing(self):
        # Draw the main gameplay scene
        # Draw background scene image for the current scene
        current_game: Optional[Game] = self.game
        if current_game is None:
            return
        image_name = current_game.god.tree.scenes[
            current_game.current_scene_index
        ].image
        scene_img = self.scene_images.get(image_name)
        if scene_img is None:
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
        # Get current scene object
        if current_game is not None:
            try:
                current_scene: Optional[Scene] = current_game.god.tree.scenes[
                    current_game.current_scene_index
                ]
            except Exception:
                current_scene = None
        else:
            current_scene = None
        # Draw text with links
        links = []
        current_links = current_scene.links if current_scene is not None else []
        for i, link in enumerate(current_links):
            links.append(f"{string.ascii_uppercase[i]}: {link.label}")
        links_text = "\n".join(links)
        main_text = (
            f"{current_scene.text}\nPress:\n{links_text}"
            if current_scene is not None
            else "*No scene data*"
        )
        self.draw_text_word_wrap(
            main_text,
            V(-230 * self.scale, 35 * self.scale),
            self.main_font.new_size(int(self.main_font.size * self.scale)),
            Color(255, 255, 255),
            Origin.TOP_LEFT,
            wrap_distance=abs(
                self.screen_right.x - (-230 * self.scale) + (-10 * self.scale)
            ),
        )
        # Draw pause button (bottom left)
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
        # Draw pause icon (two vertical lines)
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
        """
        Draw the paused menu overlay with gameplay scene faded in the background.
        Shows pause menu buttons with resume, load, save, settings, and exit options.
        """
        if "--remove-transparency" not in self.argv:
            # Draw gameplay scene faded out behind pause menu
            self._draw_playing()
            self.fill_rect(
                self.screen_bottom_left, self.screen_top_right, Color(0, 0, 0, 150)
            )
        # Draw pause menu buttons
        buttons = ["Resume", "Load Game", "Save Game", "Settings", "Exit Game"]
        for i, button in enumerate(buttons):
            x = 0
            # Calculate y position for each button
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
            # Draw button background and outline
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
            # Draw button label
            self.draw_text(
                button,
                V(x, y),
                self.button_list_button_text_font.new_size(
                    self.button_list_button_text_font.size * self.scale
                ),
                self.button_list_button_text_color,
                Origin.CENTER,
            )
        # Draw paused title
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
        """
        Draw the load game overlay during gameplay.
        Calls the common load game renderer with in-game context.
        """
        self._draw_load_game(True)

    def _draw_settings_playing(self):
        """
        Draw the settings overlay during gameplay.
        Calls the common settings renderer with in-game context.
        """
        self._draw_settings(True)

    def draw(self):
        """
        Main draw routine called every frame.
        Clears the screen and renders the appropriate UI based on the current game state.
        """
        self.clear(Color(0, 0, 0))
        try:
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
            pass

    def on_quit(self):
        if "--disable-sound" not in self.argv:
            try:
                self.intro_boom_sound.stop()
            except Exception:
                pass


def main():
    """
    Main entry point for the Fate of the Gods application.
    Initializes the game app and starts the main game loop.
    Handles and logs any exceptions that occur during execution.
    """
    try:
        App().start()
    except Exception:
        raise


if __name__ == "__main__":
    main()
