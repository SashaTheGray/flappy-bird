"""This module contains the Speedometer class.

Speedometer controls the game speed.
"""

#################
##   IMPORTS   ##
#################

import src.utils.functions as utils
from src.exceptions import MissingConfigurationError
from src.utils.types import *


###################
##   CONSTANTS   ##
###################


class Speedometer:
    """Speed controller in the game."""

    ########################
    ##   DUNDER METHODS   ##
    ########################

    def __init__(self, config: Config) -> None:
        """Initialize a Speedometer instance."""

        self.__config: Config = config

        try:
            self.__max_speed: float = utils.get_config_value(
                self.__config, "speedometer.max_game_speed"
            )
            self.__speed: float = utils.get_config_value(
                self.__config, "speedometer.game_speed"
            )
        except MissingConfigurationError:
            raise

        # Cap speed.
        if self.__speed > self.__max_speed:
            self.__speed = self.__max_speed

    ####################
    ##   PROPERTIES   ##
    ####################

    @property
    def speed(self) -> float:
        """Get the game speed."""

        return self.__speed

    ########################
    ##   PUBLIC METHODS   ##
    ########################

    #########################
    ##   PRIVATE METHODS   ##
    #########################
