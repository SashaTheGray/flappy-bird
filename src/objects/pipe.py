"""This module contains the Pipe class.

Pipes are obstacles in the game that you aim to avoid colliding with.
"""

#################
##   IMPORTS   ##
#################

import src.utils.functions as utils
from src.exceptions import MissingConfigurationError
from src.utils.stenographer import Stenographer
from src.utils.types import *

###################
##   CONSTANTS   ##
###################

LOGGER: Stenographer = Stenographer.create_logger(stream_handler_level=30)


###############
##   CLASS   ##
###############


class Pipe(pg.sprite.Sprite):
    """Representing a pipe in the game."""

    ########################
    ##   DUNDER METHODS   ##
    ########################

    def __init__(
        self, position: Position, config: Config, reversed: bool
    ) -> None:
        """Initialize a Pipe instance."""

        LOGGER.operation("Initializing a Pipe instance")

        super(Pipe, self).__init__()

        self.__position: Position = position
        self.__config: Config = config
        self.__sprite: pg.Surface = self.__load_sprite(reversed)
        self.__rect: pg.Rect = self.__sprite.get_rect()

        if reversed:
            self.__rect.bottomleft = self.__position
        else:
            self.__rect.topleft = self.__position

        LOGGER.success("Pipe instance initialized")

    ####################
    ##   PROPERTIES   ##
    ####################

    @property
    def image(self) -> pg.Surface:
        """Getter method for self.__sprite."""

        return self.__sprite

    @property
    def rect(self) -> pg.Rect:
        """Getter method for self.__rect."""

        return self.__rect

    ########################
    ##   PUBLIC METHODS   ##
    ########################

    def update(self, speed: int) -> None:
        """Update the ground."""

        # Move the ground.
        self.__rect.x -= speed

        # Delete pipes when the go off-screen.
        if self.__rect.right < 0 - 50:
            self.kill()

    #########################
    ##   PRIVATE METHODS   ##
    #########################

    def __load_sprite(self, reversed: bool) -> pg.Surface:
        """Load the ground sprite."""

        # Get sprite path.
        try:
            sprite_path: str = utils.get_config_value(
                self.__config, "assets.images.obstacles.pipes.green"
            )
        except MissingConfigurationError:
            raise

        sprite: pg.Surface = utils.load_asset(sprite_path)

        if reversed:
            sprite = pg.transform.flip(sprite, flip_x=False, flip_y=True)

        return sprite
