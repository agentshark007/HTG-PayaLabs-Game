import panda2d


class App(panda2d.PandaApp):
    def initialize(self):
        self.ares_image = panda2d.Image("assets/ares.png")
    
    def update(self):
        pass
    
    def draw(self):
        self.clear((50, 50, 50))  # gray background
        self.fill_rect(-50, -50, 50, 50, (255, 0, 0))
        self.draw_image(self.ares_image, 0, 0, align=panda2d.Align.CENTER, anti_aliasing=False, width=self.ares_image.width * 5, height=self.ares_image.height * 5)


def main():
    application = App(
        width=800,
        height=600,
        title="HTG PayaLabs Game",
        resizable=panda2d.Resizable.NONE
    )
    
    application.run()


if __name__ == "__main__":
    main()
