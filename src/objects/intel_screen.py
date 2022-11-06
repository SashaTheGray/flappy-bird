"""This module contains the IntelScreen class."""

import src.objects.bird
from src.utils.types import *


class IntelScreen(pg.sprite.Sprite):
    """Representing the intelligence screen in the game."""

    def __init__(
        self,
        birds: Sequence[src.objects.bird.Bird],
        config: Config,
        *,
        font: str = "consolas",
        text_size: int = 12,
        text_colour: RGB = (255, 255, 255),
    ) -> None:
        """Initialize an IntelScreen instance."""

        super().__init__()

        ################
        ##   CONFIG   ##
        ################

        self.__config: Config = config
        self.__is_ai: bool = len(birds) > 1
        self.__font: str = font
        self.__text_size: int = text_size
        self.__text_colour: RGB = text_colour

        self.__score_text: str = "Score: {}"
        self.__x_dist_text: str = "Horizontal distance from pipe: {}"
        self.__y_dist_text: str = "Vertical distance from pipe: {}"

        ##################
        ##   SECTIONS   ##
        ##################

        # If human is playing.
        if not self.__is_ai:
            # Create the score section.
            self.__score_sprite: pg.Surface = self.__create_sprite(
                self.__score_text.format(0), self.__text_size
            )
            self.__score_rect: pg.Rect = self.__score_sprite.get_rect()
            self.__score_rect.topleft = (
                (self.__config["window"]["width"] - self.__score_rect.width)
                // 2,
                0.90 * self.__config["window"]["height"],
            )

    def update(self, score: int, x_from_pipe: int, y_from_pipe: int) -> None:
        """Update the Intel screen on game tick."""

        # If human is playing.
        if not self.__is_ai:
            self.__score_sprite = self.__create_sprite(
                self.__score_text.format(score), self.__text_size
            )

    def draw(self, window: pg.Surface) -> None:
        """Draw the IntelScreen onto the game window."""

        # If human is playing.
        if not self.__is_ai:
            window.blit(self.__score_sprite, self.__score_rect)

    def __create_sprite(self, text: str, size: int) -> pg.Surface:
        """Create a text sprite."""

        font: pg.font.Font = pg.font.SysFont(self.__font, size)
        sprite: pg.Surface = font.render(text, True, self.__text_colour)
        return sprite
