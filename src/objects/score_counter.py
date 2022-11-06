"""This module contains the ScoreCounter class."""

#################
##   IMPORTS   ##
#################

# Pip imports.
import pygame as pg

# Local imports.
import src.utils.functions as utils
from src.utils.stenographer import Stenographer
from src.utils.types import *

###################
##   CONSTANTS   ##
###################

LOGGER: Stenographer = Stenographer.create_logger()


###############
##   CLASS   ##
###############


class ScoreCounter(pg.sprite.Sprite):
    """Representing the score counter in the game."""

    def __init__(self, position: Position, config: Config) -> None:
        """Initialize a ScoreCounter instance."""

        LOGGER.operation("Initializing score counter")

        super().__init__()
        self.__config: Config = config
        self.__score: int = 0
        self.__last_update_score: int = 0

        LOGGER.success("Score counter initialized")

    @property
    def score(self) -> int:
        """Getter for the score."""

        return self.__score

    def increment(self) -> None:
        """Increment score."""

        self.__score += 1

    def update(self, *args: Any, **kwargs: Any) -> None:
        """On frame update methods."""

        # Return if the score hasn't changed.
        if self.__score == self.__last_update_score:
            return

    def reset(self) -> None:
        """Reset the score counter."""

        self.__score = 0

    def __construct_sprite(self) -> pg.Surface:
        """Construct the number counter."""

        ...

    def __get_number_sprite(self, number: int) -> pg.Surface:
        """Return a number sprite with the corresponding 'number'."""

        # Validate number.
        if number not in range(10):
            raise ValueError(f"Number {number} is not supported")

        # Construct path to number image.
        number_path: str = (
            self.__config.get("assets").get("images").get("number")
        ).format(number)

        return utils.load_asset(number_path)
