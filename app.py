import os.path
import shutil
import string
import sys
from datetime import datetime
from enum import Enum
from typing import Optional

from game import *
from path import *
from pgiud import *

data_directory = get_absolute_path("data/")


class InitializeError(Exception):
    pass


class UpdateError(Exception):
    pass


class DrawError(Exception):
    pass


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


class App(Window):
    def __init__(self):
        super().__init__(
            width=480,
            height=360,
            title="Fate of the Gods",
            resizable=Resizable.ASPECT,
            origin=Origin.CENTER,
        )

    def _parse_argv(self):
        raw_args = sys.argv[1:]
        self.flags = []
        self.options = {}
        for arg in raw_args:
            if arg.startswith("--"):
                if "=" in arg:
                    key, value = arg.split("=", 1)
                    self.options[key] = value
                else:
                    self.flags.append(arg)
            else:
                self.flags.append(arg)

    def set_state(self, new_state: State):
        self.state = new_state

    # region initialization
    def _initialize_saving(self):
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
        with open(default_settings_path, encoding="utf-8") as src, open(
            settings_path, "w", encoding="utf-8"
        ) as dst:
            dst.write(src.read())

    def _setup_state(self):
        if "--skip-intro" in self.flags:
            self.state = State.MAIN_MENU
        else:
            self.state = State.INTRO
        self.seconds_since_start = 0.0
        self.mouse_down_primary_last_frame = False
        self.keys_down_last_frame = set()
        self.scene_text_scroll_y = 0.0
        self.scroll_velocity = 0.0

    def _initialize_scroll_settings(self):
        self.scroll_velocity = 0.0
        self.scroll_friction = 0.85
        self.scroll_speed = -40.0
        self.scroll_min = 0.0
        self.scroll_max = 0.0

    def _load_assets(self):
        file_names = os.listdir(get_absolute_path("assets/data/scenes"))
        self.scene_images = {}
        for file_name in file_names:
            img_path = get_absolute_path(os.path.join("assets/data/scenes", file_name))
            self.scene_images[os.path.splitext(file_name)[0]] = Image(img_path)
        file_names = os.listdir(get_absolute_path("assets/data/thumbnails"))
        self.god_images = {}
        for file_name in file_names:
            img_path = get_absolute_path(
                os.path.join("assets/data/thumbnails", file_name)
            )
            self.god_images[os.path.splitext(file_name)[0]] = Image(img_path)
        self.heading_font = Font(
            get_absolute_path("assets/fonts/Silkscreen-Regular.ttf")
        )
        self.main_font = Font(get_absolute_path("assets/fonts/VT323-Regular.ttf"))
        self.intro_payalabs_logo = Image(get_absolute_path("assets/intro/payalabs.png"))
        self.intro_pgiud_logo = Image(get_absolute_path("assets/intro/pgiud.png"))
        self.intro_pygame_logo = Image(get_absolute_path("assets/intro/pygame.png"))
        if "--disable-sound" not in self.flags:
            self.intro_boom_sound = Sound(
                get_absolute_path("assets/sounds/intro_boom.mp3")
            )

    def _initialize_intro(self):
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

    def _load_data(self):
        gods_folder = get_absolute_path("assets/data/gods")
        self.god_texts: list[str] = []
        self.god_file_names: list[str] = []
        for name in os.listdir(gods_folder):
            path = os.path.join(gods_folder, name)
            if os.path.isfile(path) and name.lower().endswith(".txt"):
                try:
                    with open(path, encoding="utf-8") as f:
                        self.god_texts.append(f.read())
                        self.god_file_names.append(os.path.splitext(name)[0])
                except Exception:
                    continue
        self.gods: list[God] = []
        for i, god_text in enumerate(self.god_texts):
            try:
                self.gods.append(God(god_text, self.god_file_names[i]))
            except Exception:
                continue

    def _initialize_new_game(self):
        self.new_game_selected_god: Optional[int] = None

    def _initialize_load_game(self):
        self.load_game_selected_save: Optional[int] = None
        self.load_game_rename_mode = False
        self.load_game_rename_buffer = ""
        self.load_game_rename_index: Optional[int] = None
        self.load_game_rename_path: Optional[str] = None

    def initialize(self):
        try:
            self._parse_argv()
            self.scale = 1.0
            self._initialize_saving()
            self._setup_state()
            self._initialize_scroll_settings()
            self._load_assets()
            self._initialize_intro()
            self._initialize_button_list_settings()
            self._load_data()
            self._initialize_new_game()
            self._initialize_load_game()
        except Exception:
            raise InitializeError("Error while initializing")

    # endregion
    # region utilities
    def _reset_scene_text_scroll(self):
        self.scene_text_scroll_y = 0.0
        self.scroll_velocity = 0.0

    def _scene_text_content(self, scene: Scene):
        lines = [scene.text.strip()] if scene.text.strip() else ["*No scene data*"]
        link_lines = []
        for i, link in enumerate(scene.links):
            if i >= 26:
                break
            link_lines.append(f"{string.ascii_uppercase[i]}: {link.label}")
        if link_lines:
            if lines and lines[-1]:
                lines.append("")
            lines.append("Press:")
            lines.extend(link_lines)
        return "\n".join(lines)

    def _wrap_scene_text_lines(self, text: str, font, wrap_distance: Optional[int]):
        if not text:
            return [""]
        if wrap_distance is None or wrap_distance <= 0:
            return text.split("\n") or [""]
        lines = []
        for para in text.split("\n"):
            if para == "":
                lines.append("")
                continue
            words = para.split(" ")
            cur = ""
            for word in words:
                candidate = word if cur == "" else cur + " " + word
                try:
                    candidate_width = font.font.size(candidate)[0]
                except Exception:
                    candidate_width = 0
                if candidate_width <= wrap_distance:
                    cur = candidate
                    continue
                if cur != "":
                    lines.append(cur)
                try:
                    word_width = font.font.size(word)[0]
                except Exception:
                    word_width = 0
                if word_width <= wrap_distance:
                    cur = word
                else:
                    chunk = ""
                    for ch in word:
                        next_chunk = chunk + ch
                        try:
                            next_width = font.font.size(next_chunk)[0]
                        except Exception:
                            next_width = 0
                        if next_width <= wrap_distance:
                            chunk = next_chunk
                        else:
                            if chunk != "":
                                lines.append(chunk)
                            chunk = ch
                    cur = chunk
            if cur != "":
                lines.append(cur)
        return lines or [""]

    def _scene_text_scroll_metrics(
        self, text: str, font, wrap_distance: Optional[int], visible_height: float
    ):
        lines = self._wrap_scene_text_lines(text, font, wrap_distance)
        line_step = max(1, int(font.font.get_linesize()))
        line_height = max(1, int(font.font.get_height()))
        total_height = line_height + max(0, len(lines) - 1) * line_step
        max_scroll = max(0.0, float(total_height) - max(0.0, float(visible_height)))
        return total_height, max_scroll

    def _playing_scene_text_bottom_y(self):
        pause_button_center_y = self.screen_bottom.y + 15 * self.scale
        pause_button_radius = 10 * self.scale
        padding_above_button = 10 * self.scale
        return pause_button_center_y + pause_button_radius + padding_above_button

    def _playing_back_button_rect(self):
        return (
            V(self.screen_right.x, self.screen_bottom.y),
            V(
                self.screen_right.x - 80 * self.scale,
                self.screen_bottom.y + 26 * self.scale,
            ),
        )

    def _set_game_scene(self, game: Game, scene_index: int):
        if game is None:
            return False
        if scene_index is None:
            return False
        if not 0 <= scene_index < len(game.god.tree.scenes):
            return False
        if scene_index == game.current_scene_index:
            return False
        game.previous_scene_index = game.current_scene_index
        game.current_scene_index = scene_index
        self._reset_scene_text_scroll()
        return True

    def _clear_previous_scene(self):
        if self.game:
            self.game.previous_scene_index = None

    def _go_back_to_previous_scene(self):
        current_game: Optional[Game] = self.game
        if current_game is None:
            return False
        previous_scene_index = getattr(current_game, "previous_scene_index", None)
        if previous_scene_index is None:
            return False
        self._clear_previous_scene()
        return self._set_game_scene(current_game, previous_scene_index)

    def _selection_item_rect(self, index: int):
        return (
            V(
                self.screen_left.x + 1 * self.scale,
                self.screen_top.y
                - 1 * self.scale
                - index * 25 * self.scale
                - 30 * self.scale,
            ),
            V(
                self.screen_left.x + 149 * self.scale,
                self.screen_top.y
                - 1 * self.scale
                - index * 25 * self.scale
                - 25 * self.scale
                - 30 * self.scale,
            ),
        )

    def _action_button_rect(self, index: int):
        button_width = 180 * self.scale
        button_height = 28 * self.scale
        list_right_x = self.screen_left.x + 149 * self.scale
        x_center = list_right_x + button_width / 2
        top_y = self.screen_top.y
        return (
            V(x_center - button_width / 2, top_y - index * button_height),
            V(
                x_center + button_width / 2,
                top_y - index * button_height - button_height,
            ),
        )

    def _load_game_action_items(self, from_game: bool):
        items = [
            ("load", "Load Game"),
            ("save", "Save Game") if from_game else None,
            ("duplicate", "Duplicate Game"),
            ("delete", "Delete Game"),
            ("rename", "Rename Game"),
        ]
        return [item for item in items if item is not None]

    def _current_date_string(self):
        return datetime.now().strftime("%m/%d/%y")

    def _generate_save_file_name(self):
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        return f"save_{stamp}.txt"

    def _save_display_name(self, save_entry: dict):
        return save_entry.get("name") or save_entry.get("date", "")

    def _write_save_record(self, path: str, record: dict):
        lines = [
            f"god: {record.get('god', '')}",
            f"name: {record.get('name', record.get('date', ''))}",
            f"scene: {record.get('scene', '')}",
            f"seed: {record.get('seed', '')}",
            f"rng_draws: {record.get('rng_draws', 0)}",
            f"previous_scene: {record.get('previous_scene', '')}",
        ]
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines).strip() + "\n")

    def _save_file_path(self, file_name: str):
        return os.path.join(get_absolute_path("data/saves"), file_name)

    def _draw_selection_list(
        self,
        title: str,
        items,
        selected_index: Optional[int],
        item_label,
        empty_text: str,
    ):
        self.fill_rect(
            V(self.screen_left.x, self.screen_top.y),
            V(self.screen_left.x + 150 * self.scale, self.screen_bottom.y),
            Color(30, 30, 30),
            int(2 * self.scale),
            Color(50, 50, 50),
        )
        self.draw_text(
            title,
            V(
                self.screen_left.x + 75 * self.scale,
                self.screen_top.y - 15 * self.scale,
            ),
            self.main_font.new_size(int(23 * self.scale)),
            Color(255, 255, 255),
            Origin.CENTER,
        )
        if not items:
            self.draw_text(
                empty_text,
                V(
                    self.screen_left.x + 75 * self.scale,
                    self.screen_top.y - 55 * self.scale,
                ),
                self.main_font.new_size(int(18 * self.scale)),
                Color(180, 180, 180),
                Origin.CENTER,
            )
            return
        for i, item in enumerate(items):
            a, b = self._selection_item_rect(i)
            hover = is_point_in_rect(self.mouse_pos, a, b)
            if hover and selected_index == i:
                color = Color(60, 60, 60)
            elif hover:
                color = Color(50, 50, 50)
            elif selected_index == i:
                color = Color(50, 50, 50)
            else:
                color = Color(40, 40, 40)
            self.fill_rect(a, b, color)
            self.draw_text(
                item_label(item),
                V(
                    self.screen_left.x + 75 * self.scale,
                    self.screen_top.y - 25 * self.scale * i - 30 * self.scale,
                ),
                self.main_font.new_size(int(23 * self.scale)),
                Color(200, 220, 200),
                Origin.TOP,
            )

    def _update_selection_list(self, items, selected_index: Optional[int]):
        for i, _item in enumerate(items):
            a, b = self._selection_item_rect(i)
            hover = is_point_in_rect(self.mouse_pos, a, b)
            if hover and self.mouse_pressed:
                return i
        return selected_index

    def _load_save_entries(self):
        saves_folder = get_absolute_path("data/saves")
        save_entries = []
        if not os.path.isdir(saves_folder):
            return save_entries
        for file_name in sorted(os.listdir(saves_folder)):
            path = os.path.join(saves_folder, file_name)
            if not os.path.isfile(path) or not file_name.lower().endswith(".txt"):
                continue
            try:
                with open(path, encoding="utf-8") as f:
                    lines = split_nonempty_lines(f.read())
            except Exception:
                continue
            god_name = ""
            save_name = ""
            save_date = ""
            save_scene = ""
            save_seed = None
            save_rng_draws = 0
            save_previous_scene = None
            for line in lines:
                if line.startswith("god: "):
                    god_name = line.removeprefix("god: ").strip()
                elif line.startswith("name: "):
                    save_name = line.removeprefix("name: ").strip()
                elif line.startswith("date: "):
                    save_date = line.removeprefix("date: ").strip()
                elif line.startswith("scene: "):
                    save_scene = line.removeprefix("scene: ").strip()
                elif line.startswith("seed: "):
                    seed_value = line.removeprefix("seed: ").strip()
                    try:
                        save_seed = int(seed_value)
                    except Exception:
                        save_seed = None
                elif line.startswith("rng_draws: "):
                    draws_value = line.removeprefix("rng_draws: ").strip()
                    try:
                        save_rng_draws = int(draws_value)
                    except Exception:
                        save_rng_draws = 0
                elif line.startswith("previous_scene: "):
                    previous_value = line.removeprefix("previous_scene: ").strip()
                    try:
                        save_previous_scene = int(previous_value)
                    except Exception:
                        save_previous_scene = None
            if not god_name:
                continue
            if not save_name:
                save_name = save_date or god_name
            save_entries.append(
                {
                    "file_name": file_name,
                    "path": path,
                    "god": god_name,
                    "name": save_name,
                    "date": save_date,
                    "scene": save_scene,
                    "seed": save_seed,
                    "rng_draws": save_rng_draws,
                    "previous_scene": save_previous_scene,
                }
            )
        return save_entries

    def _find_god_by_name(self, god_name: str):
        for god in getattr(self, "gods", []):
            if god.name == god_name:
                return god
        return None

    def _clamp_load_selection(self, save_entries):
        if not save_entries:
            self.load_game_selected_save = None
            return
        if self.load_game_selected_save is None:
            self.load_game_selected_save = 0
            return
        self.load_game_selected_save = max(
            0, min(self.load_game_selected_save, len(save_entries) - 1)
        )

    def _selected_save_entry(self, save_entries):
        if self.load_game_selected_save is None:
            return None
        if not 0 <= self.load_game_selected_save < len(save_entries):
            return None
        return save_entries[self.load_game_selected_save]

    def _apply_save_to_game(self, save_entry: dict, use_seed: bool = True):
        selected_god = self._find_god_by_name(save_entry.get("god", ""))
        if selected_god is None:
            return False
        seed = (
            save_entry.get("seed")
            if use_seed
            else random.SystemRandom().randrange(1, 2**63)
        )
        if seed is None:
            seed = random.SystemRandom().randrange(1, 2**63)
        self.game = Game(
            selected_god,
            scene_id=save_entry.get("scene") or None,
            seed=seed,
            rng_draws=save_entry.get("rng_draws", 0),
            previous_scene_index=save_entry.get("previous_scene"),
        )
        self._reset_scene_text_scroll()
        self.set_state(State.PLAYING)
        return True

    def _create_save_entry_from_game(self, game: Game, display_name: str = None):
        try:
            current_scene = game.god.tree.scenes[game.current_scene_index]
        except Exception:
            current_scene = None
        date_string = self._current_date_string()
        if display_name is None:
            display_name = f"{game.god.name} {date_string}".strip()
        return {
            "god": game.god.name,
            "name": display_name,
            "scene": current_scene.id if current_scene is not None else "",
            "seed": game.seed,
            "rng_draws": game.rng_draws,
            "previous_scene": game.previous_scene_index,
        }

    def _save_new_game_entry(self, game: Game, display_name: str = None):
        record = self._create_save_entry_from_game(game, display_name)
        file_name = self._generate_save_file_name()
        path = self._save_file_path(file_name)
        self._write_save_record(path, record)
        return file_name

    def _rename_save_entry(self, save_entry: dict, new_name: str):
        record = dict(save_entry)
        record["name"] = (
            new_name.strip() if new_name.strip() else self._save_display_name(record)
        )
        self._write_save_record(save_entry["path"], record)

    def _duplicate_save_entry(self, save_entry: dict):
        new_record = dict(save_entry)
        new_record["name"] = (
            f"{new_record.get('god', '')} {self._current_date_string()}".strip()
        )
        new_file_name = self._generate_save_file_name()
        self._write_save_record(self._save_file_path(new_file_name), new_record)
        return new_file_name

    def _delete_save_entry(self, save_entry: dict):
        try:
            os.remove(save_entry["path"])
        except Exception:
            pass

    def _begin_rename_mode(self, save_entry: dict):
        self.load_game_rename_mode = True
        self.load_game_rename_index = self.load_game_selected_save
        self.load_game_rename_path = save_entry.get("path")
        self.load_game_rename_buffer = self._save_display_name(save_entry)

    def _cancel_rename_mode(self):
        self.load_game_rename_mode = False
        self.load_game_rename_index = None
        self.load_game_rename_path = None
        self.load_game_rename_buffer = ""

    def _rename_target_save_entry(self, save_entries):
        if self.load_game_rename_path:
            for save_entry in save_entries:
                if save_entry.get("path") == self.load_game_rename_path:
                    return save_entry
        return self._selected_save_entry(save_entries)

    def _commit_rename_mode(self, save_entries):
        selected_entry = self._rename_target_save_entry(save_entries)
        if selected_entry is None:
            self._cancel_rename_mode()
            return
        self._rename_save_entry(selected_entry, self.load_game_rename_buffer)
        self._cancel_rename_mode()

    def _rename_text_from_key(self, key_enum):
        shift_down = self.keydown(Key.LSHIFT) or self.keydown(Key.RSHIFT)
        mapping = {
            Key.SPACE: " ",
            Key.MINUS: "_" if shift_down else "-",
            Key.EQUALS: "+" if shift_down else "=",
            Key.PERIOD: ">" if shift_down else ".",
            Key.COMMA: "<" if shift_down else ",",
            Key.SLASH: "?" if shift_down else "/",
            Key.APOSTROPHE: '"' if shift_down else "'",
            Key.BACKSLASH: "|" if shift_down else "\\",
            Key.LEFTBRACKET: "{" if shift_down else "[",
            Key.RIGHTBRACKET: "}" if shift_down else "]",
            Key.GRAVE: "~" if shift_down else "`",
            Key.NUM_0: "0",
            Key.NUM_1: "1",
            Key.NUM_2: "2",
            Key.NUM_3: "3",
            Key.NUM_4: "4",
            Key.NUM_5: "5",
            Key.NUM_6: "6",
            Key.NUM_7: "7",
            Key.NUM_8: "8",
            Key.NUM_9: "9",
        }
        if key_enum in mapping:
            return mapping[key_enum]
        if key_enum.name in string.ascii_uppercase:
            return key_enum.name if shift_down else key_enum.name.lower()
        return None

    def _update_rename_mode(self, save_entries):
        if self.load_game_rename_index is None:
            self._cancel_rename_mode()
            return
        escape_pressed = (
            self.keydown(Key.ESCAPE) and Key.ESCAPE not in self.keys_down_last_frame
        )
        if escape_pressed:
            self._cancel_rename_mode()
            return
        enter_keys = [Key.ENTER]
        try:
            enter_keys.append(Key.KP_ENTER)
        except Exception:
            pass
        enter_pressed = any(
            (
                self.keydown(key_enum) and key_enum not in self.keys_down_last_frame
                for key_enum in enter_keys
            )
        )
        if enter_pressed:
            self._commit_rename_mode(save_entries)
            return
        delete_keys = [Key.BACKSPACE]
        try:
            delete_keys.append(Key.DELETE)
        except Exception:
            pass
        delete_pressed = any(
            (
                self.keydown(key_enum) and key_enum not in self.keys_down_last_frame
                for key_enum in delete_keys
            )
        )
        if delete_pressed:
            if self.load_game_rename_buffer:
                self.load_game_rename_buffer = self.load_game_rename_buffer[:-1]
            return
        tracked_keys = self._tracked_keys()
        for key_enum in tracked_keys:
            if key_enum in {
                Key.BACKSPACE,
                Key.DELETE,
                Key.ENTER,
                Key.KP_ENTER,
                Key.ESCAPE,
                Key.LSHIFT,
                Key.RSHIFT,
            }:
                continue
            if key_enum in self.keys_down_last_frame:
                continue
            if self.keydown(key_enum):
                char = self._rename_text_from_key(key_enum)
                if char is not None:
                    self.load_game_rename_buffer += char

    def _tracked_keys(self):
        keys = []
        for i in range(26):
            try:
                keys.append(Key[chr(ord("A") + i)])
            except Exception:
                pass
        for name in [
            "NUM_0",
            "NUM_1",
            "NUM_2",
            "NUM_3",
            "NUM_4",
            "NUM_5",
            "NUM_6",
            "NUM_7",
            "NUM_8",
            "NUM_9",
            "SPACE",
            "MINUS",
            "EQUALS",
            "PERIOD",
            "COMMA",
            "SLASH",
            "APOSTROPHE",
            "BACKSLASH",
            "LEFTBRACKET",
            "RIGHTBRACKET",
            "GRAVE",
            "BACKSPACE",
            "DELETE",
            "ENTER",
            "KP_ENTER",
            "ESCAPE",
            "LSHIFT",
            "RSHIFT",
        ]:
            try:
                keys.append(Key[name])
            except Exception:
                pass
        return keys

    def _draw_god_detail_panel(self, god: God):
        self.fill_rect(
            V(self.screen_right.x, self.screen_top.y),
            V(
                self.screen_right.x - 130 * self.scale,
                self.screen_top.y - 150 * self.scale,
            ),
            Color(30, 30, 30),
            int(2 * self.scale),
            Color(50, 50, 50),
        )
        self.fill_rect(
            V(self.screen_left.x + 150 * self.scale, self.screen_top.y),
            V(
                self.screen_right.x - 130 * self.scale,
                self.screen_top.y - 150 * self.scale,
            ),
            Color(0, 0, 0),
        )
        self.fill_rect(
            V(
                self.screen_left.x + 150 * self.scale,
                self.screen_top.y - 150 * self.scale,
            ),
            V(self.screen_right.x, self.screen_bottom.y),
            Color(0, 0, 0),
        )
        try:
            self.draw_image(
                self.god_images[god.image],
                V(
                    self.screen_right.x - 65 * self.scale,
                    self.screen_top.y - 75 * self.scale,
                ),
                origin=Origin.CENTER,
                scale_x=self.scale
                * 1.5
                * (math.sin(self.seconds_since_start * 2) * 0.1 + 0.9),
                scale_y=self.scale * 1.5,
            )
        except Exception:
            pass
        self.draw_text(
            god.name,
            V(
                self.screen_left.x + 155 * self.scale + 3 * self.scale,
                self.screen_top.y,
            ),
            self.heading_font.new_size(int(25 * self.scale)),
            Color(255, 255, 255),
            Origin.TOP_LEFT,
        )
        self.draw_text_word_wrap(
            god.info,
            V(
                self.screen_left.x + 155 * self.scale + 3 * self.scale,
                self.screen_top.y - 155 * self.scale + 3 * self.scale,
            ),
            self.main_font.new_size(int(30 * self.scale)),
            Color(255, 255, 255),
            Origin.TOP_LEFT,
            wrap_distance=abs(
                self.screen_left.x
                - (self.screen_left.x + 155 * self.scale + 3 * self.scale)
            )
            * 2,
        )

    def _parse_weighted_targets(self, raw_target: str):
        parsed_targets = []
        for token in raw_target.split(","):
            option = token.strip()
            if not option:
                continue
            target_id = option
            weight = 1.0
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
        current_game = getattr(self, "game", None)
        total_weight = sum((weight for _, weight in weighted_targets))
        if total_weight <= 0:
            return None
        if current_game is not None:
            roll = current_game.rng.random() * total_weight
            current_game.rng_draws += 1
        else:
            roll = random.random() * total_weight
        running = 0.0
        for target_id, weight in weighted_targets:
            running += weight
            if roll < running:
                return target_id
        return weighted_targets[-1][0]

    # endregion
    # region update
    def _update_load_game(self, from_game: bool):
        save_entries = self._load_save_entries()
        if self.load_game_rename_mode:
            self._update_rename_mode(save_entries)
            return
        self.load_game_selected_save = self._update_selection_list(
            save_entries, self.load_game_selected_save
        )
        self._clamp_load_selection(save_entries)
        selected_save = self._selected_save_entry(save_entries)
        clicked = None
        for index, (action_key, _label) in enumerate(
            self._load_game_action_items(from_game)
        ):
            a, b = self._action_button_rect(index)
            if is_point_in_rect(self.mouse_pos, a, b) and self.mouse_pressed:
                clicked = action_key
                break
        if clicked == "save" and self.game is not None:
            new_file_name = self._save_new_game_entry(self.game)
            save_entries = self._load_save_entries()
            self.load_game_selected_save = next(
                (
                    i
                    for i, save in enumerate(save_entries)
                    if save["file_name"] == new_file_name
                ),
                self.load_game_selected_save,
            )
            return
        if clicked and selected_save is not None:
            if clicked == "load":
                self._apply_save_to_game(selected_save)
                return
            if clicked == "duplicate":
                new_file_name = self._duplicate_save_entry(selected_save)
                save_entries = self._load_save_entries()
                self.load_game_selected_save = next(
                    (
                        i
                        for i, save in enumerate(save_entries)
                        if save["file_name"] == new_file_name
                    ),
                    self.load_game_selected_save,
                )
                return
            if clicked == "rename":
                self._begin_rename_mode(selected_save)
                return
            if clicked == "delete":
                self._delete_save_entry(selected_save)
                save_entries = self._load_save_entries()
                self._clamp_load_selection(save_entries)
                return
        hover = is_point_in_rect(
            self.mouse_pos,
            V(self.screen_right.x, self.screen_bottom.y),
            V(
                self.screen_right.x - 130 * self.scale,
                self.screen_bottom.y + 40 * self.scale,
            ),
        )
        if hover:
            if self.mouse_pressed:
                if from_game:
                    self.set_state(State.PAUSED)
                else:
                    self.set_state(State.MAIN_MENU)

    def _update_settings(self, from_game: bool):
        hover = is_point_in_rect(
            self.mouse_pos,
            V(self.screen_right.x, self.screen_bottom.y),
            V(
                self.screen_right.x - 130 * self.scale,
                self.screen_bottom.y + 40 * self.scale,
            ),
        )
        if hover:
            if self.mouse_pressed:
                if from_game:
                    self.set_state(State.PAUSED)
                else:
                    self.set_state(State.MAIN_MENU)

    def _update_intro(self):
        self.intro_current_logo_time += self.deltatime
        num_logos = len(self.intro_logos)
        if self.intro_current_logo_index == 0:
            if self.intro_current_logo_time > self.intro_pre_delay:
                self.intro_current_logo_index = 1
                self.intro_current_logo_time = 0
                if "--disable-sound" not in self.flags:
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
                    if "--disable-sound" not in self.flags:
                        try:
                            if self.intro_boom_sound:
                                self.intro_boom_sound.play()
                        except Exception:
                            pass
        elif self.intro_current_logo_index == num_logos + 1:
            if self.intro_current_logo_time > self.intro_post_delay:
                self.set_state(State.MAIN_MENU)

    def _update_credits(self):
        hover = is_point_in_rect(
            self.mouse_pos,
            V(self.screen_right.x, self.screen_bottom.y),
            V(
                self.screen_right.x - 130 * self.scale,
                self.screen_bottom.y + 40 * self.scale,
            ),
        )
        if hover:
            if self.mouse_pressed:
                self.set_state(State.MAIN_MENU)

    def _update_quit(self):
        self._running = False

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
                    self.button_list_button_top_offset
                    + self.button_list_button_height / 2
                    + i
                    * (self.button_list_button_height + self.button_list_button_padding)
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
        self.new_game_selected_god = self._update_selection_list(
            self.gods, self.new_game_selected_god
        )
        back_x = self.screen_left.x + 150 * self.scale
        back_hover = is_point_in_rect(
            self.mouse_pos,
            V(back_x, self.screen_bottom.y),
            V(back_x + 130 * self.scale, self.screen_bottom.y + 40 * self.scale),
        )
        if back_hover and self.mouse_pressed:
            self.set_state(State.MAIN_MENU)
            return
        hover = is_point_in_rect(
            self.mouse_pos,
            V(self.screen_right.x, self.screen_bottom.y),
            V(
                self.screen_right.x - 130 * self.scale,
                self.screen_bottom.y + 40 * self.scale,
            ),
        )
        if hover and self.mouse_pressed and (self.new_game_selected_god is not None):
            self.game = Game(self.gods[self.new_game_selected_god])
            self._reset_scene_text_scroll()
            self.set_state(State.PLAYING)

    def _update_load_game_menu(self):
        self._update_load_game(False)

    def _update_settings_menu(self):
        self._update_settings(False)

    def _update_playing(self):
        current_game: Optional[Game] = self.game

        # back button (scene history)
        back_a, back_b = self._playing_back_button_rect()
        back_enabled = (
            current_game is not None
            and getattr(current_game, "previous_scene_index", None) is not None
            and (current_game.previous_scene_index != current_game.current_scene_index)
        )

        if back_enabled and is_point_in_rect(self.mouse_pos, back_a, back_b):
            if self.mouse_pressed and self._go_back_to_previous_scene():
                current_game.previous_scene_index = None
                return

        # pause button
        hover = (
            distance(
                self.mouse_pos,
                V(
                    self.screen_left.x + 15 * self.scale,
                    self.screen_bottom.y + 15 * self.scale,
                ),
            )
            < 10 * self.scale
        )
        if hover and self.mouse_pressed:
            self.set_state(State.PAUSED)

        if current_game is None:
            return

        try:
            current_scene: Optional[Scene] = current_game.god.tree.scenes[
                current_game.current_scene_index
            ]
        except Exception:
            current_scene = None

        if current_scene is None:
            self._reset_scene_text_scroll()
            return

        # LINK INPUT
        if current_scene.links:
            for i, link in enumerate(current_scene.links):
                if i >= 26:
                    break

                key_name = chr(ord("A") + i)
                try:
                    key_enum = Key[key_name]
                except Exception:
                    continue

                pressed_now = self.keydown(key_enum)
                was_pressed = key_enum in self.keys_down_last_frame

                if pressed_now and (not was_pressed):
                    target_id = self._choose_target_id(link.target)
                    if target_id is None:
                        continue

                    for idx, scene in enumerate(current_game.god.tree.scenes):
                        if scene.id == target_id:
                            self._set_game_scene(current_game, idx)
                            break

        # SCROLL PHYSICS
        self.scene_text_scroll_y += self.scroll_velocity * self.deltatime
        self.scroll_velocity *= self.scroll_friction

        # clamp using computed max
        self.scene_text_scroll_y = max(
            0.0, min(self.scene_text_scroll_y, self.scroll_max)
        )

        if (
            self.scene_text_scroll_y <= 0.0
            or self.scene_text_scroll_y >= self.scroll_max
        ):
            self.scroll_velocity = 0.0

    def _update_paused(self):
        actions = [
            ("resume", State.PLAYING),
            ("load", State.LOAD_GAME_PLAYING),
            ("save", State.LOAD_GAME_PLAYING),
            ("settings", State.SETTINGS_PLAYING),
            ("exit", State.MAIN_MENU),
        ]
        for i, (_action, target_state) in enumerate(actions):
            x = 0
            y = (
                self.screen_top.y
                - (
                    self.button_list_button_top_offset
                    + self.button_list_button_height / 2
                    + i
                    * (self.button_list_button_height + self.button_list_button_padding)
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
                self.set_state(target_state)

    def _update_load_game_playing(self):
        self._update_load_game(True)

    def _update_settings_playing(self):
        self._update_settings(True)

    def update(self):
        self.mouse_pressed = self.mouse_down_primary and (
            not self.mouse_down_primary_last_frame
        )
        scale_x = self.width / self._original_width
        scale_y = self.height / self._original_height
        self.scale = (scale_x + scale_y) / 2.0
        self.seconds_since_start += self.deltatime

        # ADD: scroll input -> velocity
        self.scroll_velocity += self.mouse_scroll_y * self.scroll_speed

        try:
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
            raise UpdateError("Error while updating state: " + str(self.state))

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

        if self.load_game_rename_mode:
            all_rename_keys = self._tracked_keys()
            for key_enum in all_rename_keys:
                if self.keydown(key_enum):
                    new_keys.add(key_enum)
            self.keys_down_last_frame = new_keys

    # endregion
    # region draw
    def _draw_load_game(self, from_game: bool):
        if from_game:
            if "--remove-transparency" not in self.flags:
                self._draw_playing()
                self.fill_rect(
                    self.screen_bottom_left, self.screen_top_right, Color(0, 0, 0, 150)
                )
        save_entries = self._load_save_entries()
        selected_save = self._selected_save_entry(save_entries)
        self._draw_selection_list(
            "Load Game",
            save_entries,
            self.load_game_selected_save,
            lambda save: self._save_display_name(save),
            "No saves found",
        )
        if self.load_game_rename_mode:
            rename_y_offset = 10 * self.scale
            self.fill_rect(
                V(self.screen_left.x, self.screen_top.y - 150 * self.scale),
                V(self.screen_right.x, self.screen_bottom.y),
                Color(0, 0, 0),
            )
            self.draw_text(
                "Rename Save",
                V(
                    self.screen_left.x + 10 * self.scale,
                    self.screen_top.y - 170 * self.scale + rename_y_offset,
                ),
                self.heading_font.new_size(int(28 * self.scale)),
                Color(255, 255, 255),
                Origin.TOP_LEFT,
            )
            self.fill_rounded_rect(
                V(
                    self.screen_left.x + 10 * self.scale,
                    self.screen_top.y - 210 * self.scale + rename_y_offset,
                ),
                V(
                    self.screen_right.x - 10 * self.scale,
                    self.screen_top.y - 240 * self.scale + rename_y_offset,
                ),
                Color(40, 40, 40),
                int(1 * self.scale),
                Color(50, 50, 50),
                6 * self.scale,
                6 * self.scale,
                6 * self.scale,
                6 * self.scale,
                1,
            )
            self.draw_text(
                self.load_game_rename_buffer or "",
                V(
                    self.screen_left.x + 15 * self.scale,
                    self.screen_top.y - 220 * self.scale + rename_y_offset,
                ),
                self.main_font.new_size(int(20 * self.scale)),
                Color(255, 255, 255),
                Origin.TOP_LEFT,
            )
            self.draw_text(
                "Enter to save, Esc to cancel",
                V(
                    self.screen_left.x + 10 * self.scale,
                    self.screen_top.y - 255 * self.scale + rename_y_offset,
                ),
                self.main_font.new_size(int(14 * self.scale)),
                Color(180, 180, 180),
                Origin.TOP_LEFT,
            )
        else:
            for index, (action_key, label) in enumerate(
                self._load_game_action_items(from_game)
            ):
                a, b = self._action_button_rect(index)
                enabled = (
                    self.game is not None
                    if action_key == "save"
                    else selected_save is not None
                )
                hover = enabled and is_point_in_rect(self.mouse_pos, a, b)
                if hover and enabled:
                    button_color = Color(60, 60, 60)
                elif enabled:
                    button_color = Color(40, 40, 40)
                else:
                    button_color = Color(30, 30, 30)
                self.fill_rect(
                    a, b, button_color, int(1 * self.scale), Color(50, 50, 50)
                )
                self.draw_text(
                    label,
                    V((a.x + b.x) / 2, (a.y + b.y) / 2),
                    self.main_font.new_size(int(18 * self.scale)),
                    Color(200, 220, 200) if enabled else Color(120, 120, 120),
                    Origin.CENTER,
                )
        if not self.load_game_rename_mode:
            hover = is_point_in_rect(
                self.mouse_pos,
                V(self.screen_right.x, self.screen_bottom.y),
                V(
                    self.screen_right.x - 130 * self.scale,
                    self.screen_bottom.y + 40 * self.scale,
                ),
            )
            self.fill_rounded_rect(
                V(self.screen_right.x, self.screen_bottom.y),
                V(
                    self.screen_right.x - 130 * self.scale,
                    self.screen_bottom.y + 40 * self.scale,
                ),
                Color(40, 40, 40) if hover else Color(30, 30, 30),
                int(2 * self.scale),
                Color(50, 50, 50),
                top_left_roundness=10 * self.scale,
            )
            self.draw_text(
                "Back",
                V(
                    self.screen_right.x - 65 * self.scale,
                    self.screen_bottom.y + 20 * self.scale,
                ),
                self.main_font.new_size(int(30 * self.scale)),
                Color(255, 255, 255),
                Origin.CENTER,
            )

    def _draw_settings(self, from_game: bool):
        if from_game:
            if "--remove-transparency" not in self.flags:
                self._draw_playing()
                self.fill_rect(
                    self.screen_bottom_left, self.screen_top_right, Color(0, 0, 0, 150)
                )
        self.draw_text(
            "No settings yet...",
            self.screen_center,
            self.main_font.new_size(int(22 * self.scale)),
            Color(220, 220, 220),
            Origin.CENTER,
        )
        hover = is_point_in_rect(
            self.mouse_pos,
            V(self.screen_right.x, self.screen_bottom.y),
            V(
                self.screen_right.x - 130 * self.scale,
                self.screen_bottom.y + 40 * self.scale,
            ),
        )
        self.fill_rounded_rect(
            V(self.screen_right.x, self.screen_bottom.y),
            V(
                self.screen_right.x - 130 * self.scale,
                self.screen_bottom.y + 40 * self.scale,
            ),
            Color(40, 40, 40) if hover else Color(30, 30, 30),
            int(1 * self.scale),
            Color(50, 50, 50),
            top_left_roundness=10 * self.scale,
        )
        self.draw_text(
            "Back",
            V(
                self.screen_right.x - 65 * self.scale,
                self.screen_bottom.y + 20 * self.scale,
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
                )
            except Exception:
                pass

    def _draw_credits(self):
        self.draw_text(
            "Credits",
            V(self.screen_top.x, self.screen_top.y - 20 * self.scale),
            self.main_font.new_size(int(30 * self.scale)),
            Color(255, 255, 255),
            Origin.CENTER,
        )
        self.draw_text(
            "Fate of the Gods\nLead Developer: Andru Cupala\nGame Designer and God Creator: Aislinn Haist\nArtist: Danielle Miless\n\nandrucupala.com/payalabs\n\nCreated with python using pygame and pgiud",
            V(self.screen_top.x, self.screen_top.y - 40 * self.scale),
            self.main_font.new_size(int(22 * self.scale)),
            Color(255, 255, 255),
            Origin.TOP,
        )
        hover = is_point_in_rect(
            self.mouse_pos,
            V(self.screen_right.x, self.screen_bottom.y),
            V(
                self.screen_right.x - 130 * self.scale,
                self.screen_bottom.y + 40 * self.scale,
            ),
        )
        self.fill_rounded_rect(
            V(self.screen_right.x, self.screen_bottom.y),
            V(
                self.screen_right.x - 130 * self.scale,
                self.screen_bottom.y + 40 * self.scale,
            ),
            Color(40, 40, 40) if hover else Color(30, 30, 30),
            int(1 * self.scale),
            Color(50, 50, 50),
            top_left_roundness=10 * self.scale,
        )
        self.draw_text(
            "Back",
            V(
                self.screen_right.x - 65 * self.scale,
                self.screen_bottom.y + 20 * self.scale,
            ),
            self.main_font.new_size(int(30 * self.scale)),
            Color(255, 255, 255),
            Origin.CENTER,
        )

    def _draw_quit(self):
        pass

    def _draw_main_menu(self):
        buttons = ["New Game", "Load Game", "Settings", "Credits", "Quit"]
        for i, button in enumerate(buttons):
            x = 0
            y = (
                self.screen_top.y
                - (
                    self.button_list_button_top_offset
                    + self.button_list_button_height / 2
                    + i
                    * (self.button_list_button_height + self.button_list_button_padding)
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
                self.button_list_button_text_font.new_size(
                    self.button_list_button_text_font.size * self.scale
                ),
                self.button_list_button_text_color,
                Origin.CENTER,
            )
        self.draw_text(
            "Fate of the Gods",
            V(
                self.screen_center.x,
                self.screen_top.y - self.button_list_title_top_offset * self.scale,
            ),
            self.button_list_title_font.new_size(
                self.button_list_title_font.size * self.scale
            ),
            self.button_list_button_text_color,
            Origin.CENTER,
        )

    def _draw_new_game(self):
        if "--god-file" in self.flags:
            self._draw_selection_list(
                "Select Your God",
                self.gods,
                self.new_game_selected_god,
                lambda god: god.file_name,
                "No gods found",
            )
        else:
            self._draw_selection_list(
                "Select Your God",
                self.gods,
                self.new_game_selected_god,
                lambda god: god.name,
                "No gods found",
            )
        if self.new_game_selected_god is not None:
            selected_god: God = self.gods[self.new_game_selected_god]
            self._draw_god_detail_panel(selected_god)
        back_x = self.screen_left.x + 150 * self.scale
        back_hover = is_point_in_rect(
            self.mouse_pos,
            V(back_x, self.screen_bottom.y),
            V(back_x + 130 * self.scale, self.screen_bottom.y + 40 * self.scale),
        )
        self.fill_rounded_rect(
            V(back_x, self.screen_bottom.y),
            V(back_x + 130 * self.scale, self.screen_bottom.y + 40 * self.scale),
            Color(40, 40, 40) if back_hover else Color(30, 30, 30),
            int(2 * self.scale),
            Color(50, 50, 50),
            top_right_roundness=10 * self.scale,
        )
        self.draw_text(
            "Back",
            V(back_x + 65 * self.scale, self.screen_bottom.y + 20 * self.scale),
            self.main_font.new_size(int(30 * self.scale)),
            Color(255, 255, 255),
            Origin.CENTER,
        )
        hover = is_point_in_rect(
            self.mouse_pos,
            V(self.screen_right.x, self.screen_bottom.y),
            V(
                self.screen_right.x - 130 * self.scale,
                self.screen_bottom.y + 40 * self.scale,
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
                self.screen_right.x - 130 * self.scale,
                self.screen_bottom.y + 40 * self.scale,
            ),
            button_color,
            int(2 * self.scale),
            Color(50, 50, 50),
            top_left_roundness=10 * self.scale,
        )
        self.draw_text(
            "Start Game",
            V(
                self.screen_right.x - 65 * self.scale,
                self.screen_bottom.y + 20 * self.scale,
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
        current_game: Optional[Game] = self.game
        if current_game is None:
            return

        try:
            current_scene: Optional[Scene] = current_game.god.tree.scenes[
                current_game.current_scene_index
            ]
        except Exception:
            current_scene = None

        main_text = "*No scene data*"
        scene_img = None

        if current_scene is not None:
            image_name = current_scene.image
            scene_img = self.scene_images.get(image_name)
            if scene_img is None:
                scene_img = self.scene_images.get("test-scene")
            main_text = self._scene_text_content(current_scene)

        text_font = self.main_font.new_size(int(self.main_font.size * self.scale))
        text_x = -230 * self.scale
        text_y = 35 * self.scale
        wrap_distance = max(1, int(abs(self.screen_right.x - text_x - 10 * self.scale)))

        text_bottom_y = self._playing_scene_text_bottom_y()
        visible_height = max(1.0, abs(text_bottom_y - text_y))

        _, max_scroll = self._scene_text_scroll_metrics(
            main_text, text_font, wrap_distance, visible_height
        )

        # ONLY store max scroll; do not clamp here
        self.scroll_max = max_scroll

        self.draw_text_word_wrap(
            main_text,
            V(text_x, text_y + self.scene_text_scroll_y),
            text_font,
            Color(255, 255, 255),
            Origin.TOP_LEFT,
            wrap_distance=wrap_distance,
        )

        if scene_img is not None:
            self.draw_image(
                scene_img,
                V(0 * self.scale, 110 * self.scale),
                origin=Origin.CENTER,
                scale_x=self.scale,
                scale_y=self.scale,
                antialiasing=False,
            )

        back_a, back_b = self._playing_back_button_rect()
        back_enabled = (
            getattr(current_game, "previous_scene_index", None) is not None
            and current_game.previous_scene_index != current_game.current_scene_index
        )

        back_hover = back_enabled and is_point_in_rect(self.mouse_pos, back_a, back_b)

        self.fill_rounded_rect(
            back_a,
            back_b,
            (
                Color(60, 60, 60)
                if back_hover
                else Color(40, 40, 40) if back_enabled else Color(25, 25, 25)
            ),
            int(1 * self.scale),
            Color(50, 50, 50),
            top_left_roundness=8 * self.scale,
        )

        self.draw_text(
            "Back",
            V((back_a.x + back_b.x) / 2, (back_a.y + back_b.y) / 2),
            self.main_font.new_size(int(16 * self.scale)),
            Color(255, 255, 255) if back_enabled else Color(120, 120, 120),
            Origin.CENTER,
        )

        hover = (
            distance(
                self.mouse_pos,
                V(
                    self.screen_left.x + 15 * self.scale,
                    self.screen_bottom.y + 15 * self.scale,
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

    def _draw_settings_playing(self):
        self._draw_settings(True)

    def _draw_paused(self):
        if "--remove-transparency" not in self.flags:
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
                    self.button_list_button_top_offset
                    + self.button_list_button_height / 2
                    + i
                    * (self.button_list_button_height + self.button_list_button_padding)
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
                self.button_list_button_text_font.new_size(
                    self.button_list_button_text_font.size * self.scale
                ),
                self.button_list_button_text_color,
                Origin.CENTER,
            )
        self.draw_text(
            "Paused",
            V(
                self.screen_center.x,
                self.screen_top.y - self.button_list_title_top_offset * self.scale,
            ),
            self.button_list_title_font.new_size(
                self.button_list_title_font.size * self.scale
            ),
            self.button_list_button_text_color,
            Origin.CENTER,
        )

    def _draw_load_game_playing(self):
        self._draw_load_game(True)

    def draw(self):
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
            raise DrawError("Error while drawing state: " + str(self.state))

    # endregion


def main():
    try:
        App().start()
    except Exception:
        raise
