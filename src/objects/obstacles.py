"""This module contains the Obstacle class."""

#################
##   IMPORTS   ##
#################

# Python core imports.
import abc

# Pip imports.
import pygame

# Local imports.
import src.utils.functions as utils
from src.utils.types import *


#################
##   CLASSES   ##
#################


class Obstacle(pygame.sprite.Sprite, metaclass=abc.ABCMeta):
    """Representing an obstacle in the game."""

    obstacles_in_game: int = 0

    def __init__(
        self, position: Position, config: Config, time_rate: int
    ) -> None:
        """Initialise an obstacle instance."""

        super().__init__()
        self._position: Position = position
        self._config: Config = config
        self._sprite: pygame.Surface | None = None
        self._rect: pygame.Rect | None = None
        self.__time_rate: int = time_rate

    @property
    def image(self) -> pygame.Surface:
        """Getter method for self.__sprite."""

        return self._sprite

    @property
    def rect(self) -> pygame.Rect:
        """Getter method for self.__rect."""

        return self._rect

    def update(self) -> None:
        """On new frame update method."""

        # Get the scroll speed of the game.
        self.rect.x -= self._config["game"]["flying_speed"] * self.__time_rate

        # Delete obstacles when they go off-screen.
        if self.rect.right < 0:
            self.kill()


class Pipe(Obstacle):
    """Representing a pipe obstacle."""

    def __init__(
        self,
        position: Position,
        config: Config,
        *,
        reversed_: bool = False,
        time_rate: int
    ) -> None:
        """Initialize a pipe instance."""

        super().__init__(position, config, time_rate)
        self._sprite: pygame.Surface = utils.load_asset(
            self._config.get("assets")
            .get("images")
            .get("obstacles")
            .get("pipes")
            .get("green")
        )
        self._rect: pygame.Rect = self._sprite.get_rect()

        # Set pipe position.
        if reversed_:
            self._sprite = pygame.transform.flip(
                self._sprite, flip_x=False, flip_y=True
            )
            self._rect.bottomleft = self._position
        else:
            self._rect.topleft = self._position
