import panda2d


class App(panda2d.PandaApp):
    def initialize(self):
        self.ares_image = panda2d.Image("assets/ares.png")
        self.test_scene = panda2d.Image("assets/test-scene.png")
        
        self.main_font = "assets/Khmer MN.ttc"
    
    def update(self):
        pass
    
    def draw(self):
        self.clear((0, 0, 0))  # Black background

        # Context image
        self.draw_image(self.test_scene, 240, 180, align=panda2d.Align.TOP_RIGHT, anti_aliasing=False)

        # Contest text
        self.draw_text(-230, 40, "Hello world!\nYou are on a plane.\nYou will crash!", (255, 255, 255),
               align=panda2d.Align.TOP_LEFT,
               font=self.main_font,
               size=24, 
               newline_spacing=20
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
