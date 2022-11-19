"""This is the main module of the software."""
import math

# Python core imports.
import pathlib
import sys
import tomllib

# Pip imports.
import pygame

# Local imports.
import src.objects.ai
import src.objects.bird
import src.objects.game
from src.utils.stenographer import Stenographer
from src.utils.types import *

#################
##   IMPORTS   ##
#################

###################
##   CONSTANTS   ##
###################


LOGGER: Stenographer = Stenographer.create_logger()
GAME_CONFIG_PATH: str = "src/config/game_config.toml"
AI_CONFIG_PATH: str = "src/config/ai_config.cfg"
GAME_CONFIG_FILE: pathlib.Path = pathlib.Path().cwd() / GAME_CONFIG_PATH
AI_CONFIG_FILE: pathlib.Path = pathlib.Path().cwd() / AI_CONFIG_PATH
GENERATIONS: int | float | None = math.inf


def __load_configurations(path: pathlib.Path) -> Config:
    """Load configurations from a configuration file."""

    # Make sure the path exists.
    if not path.exists():
        raise FileNotFoundError(f"File {path} not found")

    try:
        # Read the configurations.
        with open(path, "rb") as stream:
            configurations: dict = tomllib.load(stream)
    except tomllib.TOMLDecodeError:
        raise
    else:
        return configurations


def __play_game(game_config: Config) -> None:
    """Play the game of Flappy Bird."""

    LOGGER.info("A human player is playing the game")

    try:
        game: src.objects.game.Game = src.objects.game.Game(game_config)
        game.play()
    except pygame.error as error:
        LOGGER.warning(f"Pygame is complaining: {str(error).capitalize()}")

    LOGGER.info("Player closed the game")


def __train_ai(game_config: Config) -> None:
    """Train the AI on the game."""

    LOGGER.info("Initializing AI training sequence")

    ai: src.objects.ai.AI = src.objects.ai.AI(game_config)
    ai.train(GENERATIONS, verbose=True)


def __test_ai(game_config: Config, superior_genome: Any) -> None:
    """Test the AI on the game."""

    raise NotImplemented


##############
##   MAIN   ##
##############


def __main() -> None:
    """This is the main function of this module."""

    # Parse program arguments.
    program_arguments: Iterable[str] = sys.argv

    # Load configurations.
    try:
        game_config: Config = __load_configurations(GAME_CONFIG_FILE)
    except (ValueError, tomllib.TOMLDecodeError) as error:
        return LOGGER.critical(error)

    # Match program arguments and execute.
    match program_arguments:
        case [_, "--ai-train"]:
            return __train_ai(game_config)
        case [_, "--ai-test"]:
            raise NotImplemented
        case [_]:
            return __play_game(game_config)
        case _:
            raise ValueError(
                f"Invalid program arguments: {program_arguments[1:]}"
            )


if __name__ == "__main__":
    __main()
