from screens.button_list import ButtonList


class MainMenuScreen:
    def initialize(self, app):
        self.button_list = ButtonList()
        self.button_list.initialize(app)

    def update(self, app):
        pass

    def draw(self, app):
        self.button_list.draw(
            app,
            "Fate of the Gods",
            ["New Game", "Load Game", "Settings", "Credits", "Quit"],
        )
