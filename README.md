
# Fate of the Gods

## Description

Fate of the Gods is an open-source project currently in development. It is developed by PayaLabs, led by Andru Cupala.

Fate of the Gods is a choose-your-own-adventure style game where the player takes on the role of a greek god and makes decisions that affect their fate and the fate of their followers. The game is designed to be replayable, with multiple paths and endings based on the player's choices.

When the game is run, a window is shown with a main menu. From there, the player can start a new game and make a series of decisions to decide the fate of the god they chose.

## Project Structure

* `main.py` – Entry point for game.
* `app.py` – Main game class.
* `pgiud.py` – Graphics engine.
* `format.sh` - Formats the code for a commit.
* `assets/` – Assets folder containing images, fonts, sounds, and other resources.
* `data/` - Data folder containing saves and settings. Included in .gitignore, so it is not tracked by git.

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


## Run arguments
- `--skip-intro`: Skips the intro sequence and goes directly to the main menu.
- `--remove-transparency`: Removes the transparency of certain UI elements for better visibility.
- `--disable-sound`: Disables all sound effects and music in the game.
- `--level=X`: Sets the logging level to X, where X can be one of the following:
  - `DEBUG`: Logs detailed information for debugging purposes.
  - `INFO`: Logs general information about the game's execution.
  - `WARN`: Logs warnings about potential issues in the game.
  - `ERROR`: Logs errors that occur during the game's execution.
  - `CRITICAL`: Logs critical errors that may cause the game to crash.
  By default, the logging level is set to `WARN`.

## Contributing

Contributions are not welcome. This is a private project by PayaLabs and is not open for external contributions at this time.

## License

This project is provided under a non-commercial license by PayaLabs. See [andrucupala.com/payalabs](https://andrucupala.com/payalabs/home.html) for more information.
