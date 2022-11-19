"""This module contains the Ground class."""

from __future__ import annotations

import src.utils.functions as utils
from src.utils.stenographer import Stenographer
from src.enums import GameStateEnum
from src.utils.types import *

if TYPE_CHECKING:
    from src.objects.game import Game
    from pygame import Surface, Rect

LOGGER = Stenographer.create_logger()


@final
class Ground(pg.sprite.Sprite):
    """Representing the ground in the game."""

    # Offset for the ground sprite stretching off-screen.
    GROUND_SLIDE_OFFSET: float = 0.5

    def __init__(self, position: Position, game: Game, config: Config) -> None:
        """Initialize a Ground instance."""

        LOGGER.operation("Initializing ground")

        super().__init__()

        self.__initial_position: Position = position
        self.__position: Position = position
        self.__game: Game = game
        self.__config: Config = config
        self.__sprite: Surface = utils.load_asset(
            self.__config.get("assets").get("images").get("ground")
        )
        self.__sprite = pg.transform.scale(
            self.__sprite,
            (
                self.__config["window"]["width"]
                * (1 + self.GROUND_SLIDE_OFFSET),
                self.__sprite.get_height(),
            ),
        )
        self.__rect: Rect = self.__sprite.get_rect()
        self.__rect.topleft = self.__position

        LOGGER.success("Ground initialized")

    @property
    def image(self) -> Surface:
        return self.__sprite

    @property
    def rect(self) -> Rect:
        return self.__rect

    def draw(self, window: Surface) -> None:
        """Draw the ground on the game window."""

        window.blit(self.__sprite, self.__rect)

    def update(self) -> None:
        """Update the ground."""

        # Ground should not move if the game is over.
        if self.__game.state == GameStateEnum.OVER:
            return

        # Move the screen while the whole spite isn't visible.
        if (
            abs(self.__rect.x)
            <= self.GROUND_SLIDE_OFFSET * self.__config["window"]["height"] - 70
        ):
            self.__rect.x -= (
                self.__config["game"]["flying_speed"] * self.__game.time_rate
            )

        # Reset the sprite to its original position.
        else:
            self.__rect.topleft = self.__initial_position
