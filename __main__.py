"""This is the main module of the software."""

#################
##   IMPORTS   ##
#################

# Python core imports.
import pathlib
import pickle
import sys
import tomllib

# Pip imports.
import pygame

# Local imports.
import src.objects.ai
import src.objects.bird
import src.objects.game
from src.exceptions import MissingConfigurationError
from src.utils.stenographer import Stenographer
from src.utils.types import *

###################
##   CONSTANTS   ##
###################


LOGGER: Stenographer = Stenographer.create_logger()
GAME_CONFIG_PATH: str = "src/config/game_config.toml"
AI_CONFIG_PATH: str = "src/config/ai_config.cfg"
GAME_CONFIG_FILE: pathlib.Path = pathlib.Path().cwd() / GAME_CONFIG_PATH
AI_CONFIG_FILE: pathlib.Path = pathlib.Path().cwd() / AI_CONFIG_PATH


@overload
def __load_configurations(
    path: pathlib.Path, load_func: Callable[[BinaryIO], Config]
) -> Genotype:
    ...


def __load_configurations(
    path: pathlib.Path, load_func: Callable[[BinaryIO], Config]
) -> Config:
    """Load configurations from a configuration file."""

    # Make sure the path exists.
    if not path.exists():
        raise FileNotFoundError(f"File {path} not found")

    # Read the configurations.
    with open(path, "rb") as stream:
        configurations: dict = load_func(stream)
    return configurations


def __play_game() -> None:
    """Play the game of Flappy Bird."""

    LOGGER.info("A human player is playing the game")

    try:
        game_config: Config = __load_configurations(
            GAME_CONFIG_FILE, tomllib.load
        )
        game: src.objects.game.Game = src.objects.game.Game(game_config)
        game.play()
    except pygame.error as error:
        LOGGER.warning(f"Pygame is complaining: {str(error).capitalize()}")
    except MissingConfigurationError as error:
        LOGGER.critical(str(error))

    LOGGER.info("Player closed the game")


def __train_ai() -> None:
    """Train the AI on the game."""

    LOGGER.info("Initializing AI training sequence")

    try:
        game_config: Config = __load_configurations(
            GAME_CONFIG_FILE, tomllib.load
        )
        ai: src.objects.ai.NeatAITrain = src.objects.ai.NeatAITrain(game_config)
        game: src.objects.game.Game = src.objects.game.Game(game_config, ai)
        ai.train(game)
    except MissingConfigurationError as error:
        LOGGER.critical(str(error))


def __test_ai(genome_file: str) -> None:
    """Test the AI on the game."""

    LOGGER.info("Initializing AI testing sequence")

    try:
        game_config: Config = __load_configurations(
            GAME_CONFIG_FILE, tomllib.load
        )
        superior_genome: Genotype = __load_configurations(
            pathlib.Path(genome_file), pickle.load
        )
        ai: src.objects.ai.NeatAITest = src.objects.ai.NeatAITest(
            [superior_genome], game_config
        )
        game: src.objects.game.Game = src.objects.game.Game(game_config, ai)
        game.play()
    except MissingConfigurationError as error:
        LOGGER.critical(str(error))
        return


##############
##   MAIN   ##
##############


def __main() -> None:
    """This is the main function of this module."""

    # Parse program arguments.
    program_arguments: Iterable[str] = sys.argv

    # Match program arguments and execute.
    match program_arguments:
        case [_, "--ai-train"]:
            return __train_ai()

        case [_, "--ai-test", genome_file]:
            return __test_ai(genome_file)

        case [_]:
            return __play_game()

        case _:
            raise ValueError(
                f"Invalid program arguments: {program_arguments[1:]}"
            )


if __name__ == "__main__":
    __main()
