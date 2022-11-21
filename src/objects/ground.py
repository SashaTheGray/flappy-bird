"""This module contains the Ground class.

This class represents the ground in the game, which you should stay above.
"""

#################
##   IMPORTS   ##
#################

from __future__ import annotations

# Local imports.
import src.utils.functions as utils
from src.enums import GameStateEnum
from src.exceptions import MissingConfigurationError
from src.utils.stenographer import Stenographer
from src.utils.types import *

if TYPE_CHECKING:
    import src.objects.game

###################
##   CONSTANTS   ##
###################

LOGGER: Stenographer = Stenographer.create_logger()


###############
##   CLASS   ##
###############


class Ground(pg.sprite.Sprite):
    """Representing the ground object in the game."""

    # Offset for the ground sprite stretching off-screen.
    __GROUND_SLIDE_OFFSET: float = 0.4

    # Ground height offset.
    __GROUND_HEIGHT_OFFSET: float = 0.85

    ########################
    ##   DUNDER METHODS   ##
    ########################

    def __init__(self, game: src.objects.game.Game, config: Config) -> None:
        """Initialize a Ground instance."""

        LOGGER.operation("Initializing Ground instance")

        super(Ground, self).__init__()

        self.__game: src.objects.game.Game = game
        self.__config: Config = config
        self.__initial_position: Position = (
            0,
            int(game.window.get_height() * self.__GROUND_HEIGHT_OFFSET),
        )
        self.__position: Position = self.__initial_position

        self.__sprite: pg.Surface = self.__load_sprite()
        self.__rect: pg.Rect = self.__sprite.get_rect()
        self.__rect.topleft = self.__position

        LOGGER.success("Ground instance initialized")

    ####################
    ##   PROPERTIES   ##
    ####################

    @property
    def image(self) -> pg.Surface:
        """Get the ground's image for drawing."""

        return self.__sprite

    @property
    def rect(self) -> pg.Rect:
        """Get the ground's collision box."""

        return self.__rect

    ########################
    ##   PUBLIC METHODS   ##
    ########################

    def update(self, speed: int) -> None:
        """Update the ground."""

        # Do not update ground when game is over.
        if self.__game.state == GameStateEnum.OVER:
            return

        # Move the screen while the whole spite isn't visible.
        if (
            abs(self.__rect.x)
            <= self.__GROUND_SLIDE_OFFSET * self.__game.window.get_width()
        ):
            self.__rect.x -= speed

        # Reset the sprite to its original position.
        else:
            self.__rect.topleft = self.__initial_position

    #########################
    ##   PRIVATE METHODS   ##
    #########################

    def __load_sprite(self) -> pg.Surface:
        """Load the ground sprite."""

        # Get sprite path.
        try:
            sprite_path: str = utils.get_config_value(
                self.__config, "assets.images.ground"
            )
        except MissingConfigurationError:
            raise

        sprite: pg.Surface = utils.load_asset(sprite_path)
        sprite = pg.transform.scale(
            surface=sprite,
            size=(
                self.__game.window.get_width()
                * (1 + self.__GROUND_HEIGHT_OFFSET),
                sprite.get_height(),
            ),
        )

        return sprite
