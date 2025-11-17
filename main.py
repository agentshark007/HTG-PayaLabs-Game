import panda2d
from app import App

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
