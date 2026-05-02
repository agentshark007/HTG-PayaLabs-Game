import sys

from path import *
from pgiud import *
from screens import Screen
from screens.button_list import ButtonList
from screens.credits import CreditsScreen
from screens.intro import IntroScreen
from screens.load_game import LoadGameScreen
from screens.main_menu import MainMenuScreen
from screens.new_game import NewGameScreen
from screens.playing import PlayingScreen
from screens.quit import QuitScreen
from screens.settings import SettingsScreen

data_directory = get_absolute_path("data/")


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
        self.argv = sys.argv[1:]

    def _create_screens(self):
        self.credits_screen = CreditsScreen()
        self.intro_screen = IntroScreen()
        self.load_screen = LoadGameScreen()
        self.main_menu_screen = MainMenuScreen()
        self.new_game_screen = NewGameScreen()
        self.playing_screen = PlayingScreen()
        self.quit_screen = QuitScreen()
        self.settings_screen = SettingsScreen()

    def _initialize_screens(self):
        self.credits_screen.initialize(self)
        self.intro_screen.initialize(self)
        self.load_screen.initialize(self)
        self.main_menu_screen.initialize(self)
        self.new_game_screen.initialize(self)
        self.playing_screen.initialize(self)
        self.quit_screen.initialize(self)
        self.settings_screen.initialize(self)

    def _initialize_state(self):
        if "--skip-intro" in self.argv:
            self.screen = Screen.MAIN_MENU
        else:
            self.screen = Screen.INTRO
        self.seconds_since_start = 0.0
        self.mouse_down_primary_last_frame = False
        self.keys_down_last_frame = set()

    def _load_fonts(self):
        self.heading_font = Font(
            get_absolute_path("assets/fonts/Silkscreen-Regular.ttf")
        )
        self.main_font = Font(get_absolute_path("assets/fonts/VT323-Regular.ttf"))

    def initialize(self):
        self._parse_argv()
        self._load_fonts()
        self._initialize_state()
        self.scale = 1.0
        self._create_screens()
        self._initialize_screens()

    def _update_current_screen(self):
        if self.screen == Screen.CREDITS:
            self.credits_screen.update(self)
        elif self.screen == Screen.INTRO:
            self.intro_screen.update(self)
        elif self.screen == Screen.LOAD_GAME:
            self.load_screen.update(self)
        elif self.screen == Screen.MAIN_MENU:
            self.main_menu_screen.update(self)
        elif self.screen == Screen.NEW_GAME:
            self.new_game_screen.update(self)
        elif self.screen == Screen.PLAYING:
            self.playing_screen.update(self)
        elif self.screen == Screen.QUIT:
            self.quit_screen.update(self)
        elif self.screen == Screen.SETTINGS:
            self.settings_screen.update(self)

    def update(self):
        self._update_current_screen()

    def _draw_current_screen(self):
        if self.screen == Screen.CREDITS:
            self.credits_screen.draw(self)
        elif self.screen == Screen.INTRO:
            self.intro_screen.draw(self)
        elif self.screen == Screen.LOAD_GAME:
            self.load_screen.draw(self)
        elif self.screen == Screen.MAIN_MENU:
            self.main_menu_screen.draw(self)
        elif self.screen == Screen.NEW_GAME:
            self.new_game_screen.draw(self)
        elif self.screen == Screen.PLAYING:
            self.playing_screen.draw(self)
        elif self.screen == Screen.QUIT:
            self.quit_screen.draw(self)
        elif self.screen == Screen.SETTINGS:
            self.settings_screen.draw(self)

    def draw(self):
        self.clear(Color(0, 0, 0))
        self._draw_current_screen()


def main():
    try:
        App().start()
    except Exception:
        raise
