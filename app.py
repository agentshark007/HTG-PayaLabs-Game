import panda2d

class App(panda2d.PandaApp):
    def initialize(self):
        pass
    
    def update(self):
        pass
    
    def draw(self):
        self.clear((50, 50, 50))  # gray background
        self.fill_rect(-50, -50, 50, 50, (255, 0, 0))
