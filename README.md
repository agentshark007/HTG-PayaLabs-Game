
# Fate of the Gods

## Description
Fate of the Gods is an open-source project currently in development. It is developed by PayaLabs, led by Andru Cupala.

When you run the game, it opens a window and displays a test scene image, sample heading and main text, and uses custom fonts. The game currently does not have gameplay, story, or interactive mechanics yet.

## Project Structure

* `main.py` – Entry point for game.
* `app.py` – Main game class.
* `pgiud.py` – Graphics engine.
* `remove_blank_lines.py` - Format assist program to clear blank lines.
* `format.sh` - Formats the code for a commit.
* `assets/` – Assets folder containing images, fonts, sounds, and other resources.

## Usage

1. Install Python (3.12.10) and dependencies:

   ```zsh
   pip install -r requirements.txt
   ```

`pgiud` version `1.3` is included in the repository, so you do not need to install it separately.

## Developers
All developers listed here are part of PayaLabs.

- Game designer: Aislinn Haist
- Artist: Danielle Milless
- Coder: Andru Cupala

## Notes

- The codebase is regularly formatted with `format.sh`. Run it before making a commit.
- Branches
  - `development`: Used during active development and contains the latest code. Very unstable and likely doesn't work at all.
  - `feature`: Used after a feature is complete. Unstable, but usually works without errors.
  - `htg-progress-report`: Created as a version branch for the history through games progress report.

## Contributing

Contributions are not welcome. This is a private project by PayaLabs and is not open for external contributions at this time.

## License

This project is provided under a non-commercial license by PayaLabs. See [andrucupala.com/payalabs](https://andrucupala.com/payalabs/home.html) for more information.
