
# Fate of the Gods

## Description

`Fate of the Gods` is an in-development choose-your-own-adventure game by PayaLabs, led by Andru Cupala.

The player takes on the role of a Greek god and makes decisions that affect the god's fate and the fate of their followers. The game is designed to be replayable, with multiple paths and endings based on the player's choices.

When the game starts, a window opens to the main menu. From there, the player can start a new game, load a save, change settings, or view the available story paths.

## Project structure

- `main.py` – Small launcher that calls `app.main()`.
- `app.py` – Main game module and `App` class.
- `pgiud.py` – Bundled graphics/input engine used by the game.
- `rbl.py` – Removes blank lines from code files; used by `format.sh`.
- `format.sh` – Formatting helper for commits.
- `requirements.txt` – Python dependencies.
- `assets/` – Bundled game content:
  - `assets/fonts/` – UI fonts.
  - `assets/images/intro/` – Intro logos.
  - `assets/images/god/` – God portraits.
  - `assets/images/scene/` – Scene background images.
  - `assets/sounds/` – Sound effects and music.
  - `assets/data/gods/` – Story data files for each god.
- `data/` – Runtime data created and modified while the game runs:
  - `data/settings.txt`
  - `data/saves/`

## Requirements

- Python 3.12.10
- Dependencies from `requirements.txt`

Install dependencies with:

```zsh
pip install -r requirements.txt
```

`pgiud` version `1.3` is included in the repository, so you do not need to install it separately.

## Running the game

From the repository root, run:

```zsh
python main.py
```

`main.py` is the recommended entry point. Running `python app.py` also works because `app.py` exposes the same `main()` function.

## Run arguments

Supported command-line options:

- `--skip-intro` – Skip the intro sequence and go directly to the main menu.
- `--remove-transparency` – Remove transparency from certain UI overlays for better visibility.
- `--disable-sound` – Disable all sound effects and music.

Notes:

- Logging is currently initialized at `DEBUG` level in `app.py`.
- `--level=X` is not currently wired up by the runtime, so it is not documented as a supported option.

## Runtime data

- The `data/` folder is used for saves and settings and must remain writable.
- Save files can be cleared from the in-game settings menu.
- Story content is loaded from `assets/data/gods/` at startup.

## Notes

- The codebase is regularly formatted with `format.sh`.
- The repository currently contains a font file named `assets/fonts/Silkscreen-Regular.ttf`, while `app.py` references `assets/fonts/Silkscene-Regular.ttf` for the heading font. If startup fails while loading fonts, check that filename first.

## Developers

All developers listed here are part of PayaLabs.

- Game designer: Aislinn Haist
- Artist: Danielle Milless
- Coder: Andru Cupala

## Contributing

Contributions are not accepted. This is a private project by PayaLabs and is not open for external contributions at this time.

## License

This project is provided under a non-commercial license by PayaLabs. See [andrucupala.com/payalabs](https://andrucupala.com/payalabs/home.html) for more information.
