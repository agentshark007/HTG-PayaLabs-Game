from elements.button_list import ButtonList
from screens import Screen


class MainMenuScreen:
    def initialize(self, app):
        self.button_list = ButtonList()
        self.button_list.initialize(app)

    def load(self, app, args):
        pass

    def update(self, app):
        self.button_list.update(
            app,
            [
                Screen.NEW_GAME,
                Screen.LOAD_GAME,
                Screen.SETTINGS,
                Screen.CREDITS,
                Screen.QUIT,
            ],
        )

    def draw(self, app):
        self.button_list.draw(
            app,
            "Fate of the Gods",
            ["New Game", "Load Game", "Settings", "Credits", "Quit"],
        )
