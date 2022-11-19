"""This module contains the IntelScreen class."""

from __future__ import annotations

import src.objects.bird
import src.utils.functions as utils
from src.utils.types import *

if TYPE_CHECKING:
    import src.objects.obstacles
    import src.objects.game


class IntelScreen(pg.sprite.Sprite):
    """Representing the intelligence screen in the game."""

    def __init__(
        self,
        game: src.objects.game.Game,
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

        self.__game: src.objects.game.Game = game
        self.__config: Config = config
        self.__font: str = font
        self.__text_size: int = text_size
        self.__text_colour: RGB = text_colour
        self.__score_text: str = "Score: {}"
        self.__last_score: int = 0
        self.__pos_text: str = "Pipe x-position: {}"
        self.__brood_text: str = "Birds in brood: {}"

        # Create the score section.
        self.__score_sprite: pg.Surface = self.__create_text_sprite(
            self.__score_text.format(0), self.__text_size
        )
        self.__score_rect: pg.Rect = self.__score_sprite.get_rect()
        self.__score_rect.topleft = (
            (self.__config["window"]["width"] - self.__score_rect.width) // 2,
            0.90 * self.__config["window"]["height"],
        )

        self.__pos_sprite: pg.Surface = self.__create_text_sprite(
            self.__pos_text.format(0), self.__text_size
        )
        self.__pos_rect: pg.Rect = self.__pos_sprite.get_rect()
        self.__pos_rect.topleft = (
            (self.__config["window"]["width"] - self.__pos_rect.width) // 2,
            0.925 * self.__config["window"]["height"],
        )

        self.__brood_sprite: pg.Surface = self.__create_text_sprite(
            self.__brood_text.format(0), self.__text_size
        )
        self.__brood_rect: pg.Rect = self.__brood_sprite.get_rect()
        self.__brood_rect.topleft = (
            (self.__config["window"]["width"] - self.__brood_rect.width) // 2,
            0.95 * self.__config["window"]["height"],
        )

    def update(self, score: int | None) -> None:
        """Update the Intel screen on game tick."""

        # If human is playing.
        self.__score_sprite = self.__create_text_sprite(
            self.__score_text.format(score or self.__last_score),
            self.__text_size,
        )

        if len(self.__game.obstacles):
            top, btm = utils.get_next_obstacle_pair_points(
                100, self.__game.obstacles
            )
            self.__pos_sprite = self.__create_text_sprite(
                self.__pos_text.format(top.rect.right),
                self.__text_size,
            )

        self.__brood_sprite = self.__create_text_sprite(
            self.__brood_text.format(len(self.__game.birds)), self.__text_size
        )

    def draw(self, window: pg.Surface) -> None:
        """Draw the IntelScreen onto the game window."""

        # If human is playing.
        window.blit(self.__score_sprite, self.__score_rect)
        window.blit(self.__pos_sprite, self.__pos_rect)
        window.blit(self.__brood_sprite, self.__brood_rect)

        if self.__game.is_ai:
            self.__draw_delta_lines(window)

    def __create_text_sprite(self, text: str, size: int) -> pg.Surface:
        """Create a text sprite."""

        font: pg.font.Font = pg.font.SysFont(self.__font, size)
        sprite: pg.Surface = font.render(text, True, self.__text_colour)
        return sprite

    def __draw_delta_lines(self, window: pg.Surface) -> None:
        """Draw lines between birds and the network input points."""

        line_color: str = "red"

        # There is nothing to draw if there are no birds or no obstacles.
        if not len(self.__game.birds) or not len(self.__game.obstacles):
            return

        # Determine the position of the next obstacle pair.
        top_pipe, btm_pipe = utils.get_next_obstacle_pair_points(
            100, self.__game.obstacles
        )

        pg.draw.line(
            surface=window,
            color=line_color,
            start_pos=top_pipe.rect.bottomright,
            end_pos=btm_pipe.rect.topright,
        )

        for bird in self.__game.birds:
            # Determine the points.
            top_pipe_point: Position = top_pipe.rect.bottomright
            btm_pipe_point: Position = btm_pipe.rect.topright

            # Draw line between bird and top pipe.
            pg.draw.line(
                surface=window,
                color=line_color,
                start_pos=bird.rect.center,
                end_pos=top_pipe_point,
            )

            # Draw line between bird and bottom pipe.
            pg.draw.line(
                surface=window,
                color=line_color,
                start_pos=bird.rect.center,
                end_pos=btm_pipe_point,
            )
