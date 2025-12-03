import panda2d
import os

BASE_PATH = os.path.dirname(os.path.abspath(__file__))
def asset(path):
    return os.path.join(BASE_PATH, "assets", path)



class App(panda2d.PandaApp):
    def initialize(self):
        self.ares_image = panda2d.Image(asset("ares.png"))
        self.test_scene = panda2d.Image(asset("test-scene.png"))
        
        self.test_font = asset("Khmer MN.ttc")
        self.heading_font = asset("Silkscreen-Regular.ttf")
        self.main_font = asset("VT323-Regular.ttf")
    
    def update(self):
        pass
    
    def draw(self):
        self.clear((0, 0, 0))  # Black background

        # Context image
        self.draw_image(self.test_scene, 240, 180, align=panda2d.Align.TOP_RIGHT, anti_aliasing=False)

        # Heading text
        self.draw_text(-230, 40, "Heading text", (255, 255, 255),
               align=panda2d.Align.TOP_LEFT,
               font=self.heading_font,
               size=24, 
               newline_spacing=20
               )
        
        # Main text
        self.draw_text(-230, 10, "Main text. The quick brown fox jumps over the lazy dog.", (255, 255, 255),
               align=panda2d.Align.TOP_LEFT,
               font=self.main_font,
               size=24, 
               newline_spacing=20,
               max_width=self.width / 2 - -230
               )

def main():
    application = App(
        width=480,
        height=360,
        title="HTG PayaLabs Game",
        resizable=panda2d.Resizable.SCALE
    )
    
    application.run()


if __name__ == "__main__":
    main()
