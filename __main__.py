"""This is the main module of the software."""

#################
##   IMPORTS   ##
#################

# Python core imports.
import pathlib
import sys
import tomllib

# Pip imports.
import pygame

# Local imports.
import src.objects.game
from src.utils.stenographer import Stenographer
from src.utils.types import *

###################
##   CONSTANTS   ##
###################


LOGGER: Stenographer = Stenographer.create_logger()
GAME_CONFIG_PATH: str = "src/config/game_config.toml"
AI_CONFIG_PATH: str = "src/config/ai_config.toml"
GAME_CONFIG_FILE: pathlib.Path = pathlib.Path().cwd() / GAME_CONFIG_PATH
AI_CONFIG_FILE: pathlib.Path = pathlib.Path().cwd() / AI_CONFIG_PATH


###############
##   LOGIC   ##
###############


def __load_configurations(path: pathlib.Path) -> Config:
    """Load configurations from a configuration file."""

    if not path.exists():
        raise FileNotFoundError(f"File {path} not found")

    try:
        with open(path, "rb") as stream:
            configurations: dict = tomllib.load(stream)
    except tomllib.TOMLDecodeError:
        raise
    else:
        return configurations


def __play_game(game_config: Config, ai_config: Config | None = None) -> None:
    """Play Crappy Bird."""

    LOGGER.info(f"{'AI' if ai_config is not None else 'Human'} is playing game")
    with src.objects.game.Game(game_config, ai_config) as game:
        try:
            game.play()
        except pygame.error as error:
            LOGGER.warning(f"Pygame is complaining: {str(error).capitalize()}")

    LOGGER.info("User closed the game")
    LOGGER.operation("Shutting down")


##############
##   MAIN   ##
##############


def __main() -> None:
    """This is the main function of this module."""

    # Parse program arguments.
    program_arguments: Iterable[str] = sys.argv

    try:
        # Parse configurations.
        game_config: Config = __load_configurations(GAME_CONFIG_FILE)
        ai_config: Config = __load_configurations(AI_CONFIG_FILE)
    except (ValueError, tomllib.TOMLDecodeError) as error:
        # Log error and exit program.
        LOGGER.critical(error)
        LOGGER.critical("Program is shutting down")
    else:
        # Play game.
        if "-A" in program_arguments or "--ai" in program_arguments:
            return __play_game(game_config, ai_config)
        return __play_game(game_config)


if __name__ == "__main__":
    __main()
