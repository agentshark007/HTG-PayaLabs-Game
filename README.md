
# Fate of the Gods

## Description
Fate of the Gods is an open-source project in early development. The current version is a technical demo for a future game about Greek gods, built with a custom graphics/input engine (`pgiud.py`) on top of PyGame.

When you run the game, it opens a window and displays a test scene image, sample heading and main text, and uses custom fonts. The game currently does not have gameplay, story, or interactive mechanics yet.

## Project Structure

* `main.py` – Entry point for game.
* `app.py` – Main game class.
* `pgiud.py` – Graphics engine.
* `assets/` – Assets folder containing images, fonts, sounds, and other resources.

## Usage

1. Install Python (3.12.10) and dependencies:

   ```zsh
   pip install -r requirements.txt
   ```

`pgiud` version `1.1` is included in the repository, so you do not need to install it separately.

## Notes

- The codebase is regularly formatted with `format.sh`. Run it before making a commit.

## Contributing

Contributions are not welcome. This is a private project by PayaLabs and is not open for external contributions at this time.

## License

This project is provided under a non-commercial license by PayaLabs. See [andrucupala.com/payalabs](https://andrucupala.com/payalabs/home.html) for more information.
