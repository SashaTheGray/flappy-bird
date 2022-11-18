"""This module contains the ScoreCounter class."""

#################
##   IMPORTS   ##
#################

# Pip imports.

# Local imports.
from src.utils.stenographer import Stenographer

###################
##   CONSTANTS   ##
###################

LOGGER: Stenographer = Stenographer.create_logger(
    stream_handler_level=30
)


###############
##   CLASS   ##
###############


class ScoreCounter:
    """Representing the score counter in the game."""

    def __init__(self) -> None:
        """Initialize a ScoreCounter instance."""

        LOGGER.operation("Initializing score counter")

        super().__init__()
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

    def reset(self) -> None:
        """Reset the score counter."""

        self.__score = 0
