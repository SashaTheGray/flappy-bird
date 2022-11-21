"""This module contains the Illustrator class.

The Illustrator handles everything to drawing PyGame object to the game window.
"""

#################
##   IMPORTS   ##
#################

from __future__ import annotations

# Python core imports.
import datetime
import time

# Local imports.
import src.objects.bird
import src.objects.pipe
import src.objects.ground
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


class Illustrator:
    """This class controls all drawing logic in the game."""

    __BROOD_TEXT: str = "Brood size: {}"
    __GENERATION_TEXT: str = "Generation: {}"
    __SCORE_TEST: str = "Score: {}"
    __TIME_TEXT: str = "Time elapsed: {}"

    ########################
    ##   DUNDER METHODS   ##
    ########################

    def __init__(self, game: src.objects.game.Game, config: Config) -> None:
        """Initialize an Illustrator instance."""

        LOGGER.operation("Initializing Illustrator instance")

        self.__start_time: float = time.perf_counter()
        self.__game: src.objects.game.Game = game
        self.__config: Config = config
        self.__images: dict[str, tuple[pg.Surface, pg.Rect]] = {
            "background": self.__load_background(),
            "main_menu": self.__load_main_menu(),
            "game_over": self.__load_game_over(),
        }

        try:
            self.__draw: bool = utils.get_config_value(
                self.__config, "illustrator.draw"
            )
        except MissingConfigurationError:
            LOGGER.error("Illustrator initialization failed")
            raise

        # Text config.
        self.__text_font: str = "consolas"
        self.__text_size: int = 12
        self.__text_colour: RGB = (0, 0, 0)

        # Sprite config.
        (
            self.__generation_sprite,
            self.__generation_rect,
        ) = self.__create_text_sprite(
            self.__GENERATION_TEXT.format(0), self.__text_size
        )
        self.__generation_rect.topleft = (
            10,
            self.__game.window.get_height() * 0.89,
        )

        self.__brood_sprite, self.__brood_rect = self.__create_text_sprite(
            self.__BROOD_TEXT.format(0), self.__text_size
        )
        self.__brood_rect.topleft = (10, self.__game.window.get_height() * 0.92)

        self.__score_sprite, self.__score_rect = self.__create_text_sprite(
            self.__SCORE_TEST.format(0), self.__text_size
        )
        self.__score_rect.topleft = (10, self.__game.window.get_height() * 0.95)
        self.__time_sprite, self.__time_rect = self.__create_text_sprite(
            self.__TIME_TEXT.format(0), self.__text_size
        )
        self.__time_rect.topleft = (10, self.__game.window.get_height() * 0.98)

        LOGGER.success("Illustrator instance initialized")

    ####################
    ##   PROPERTIES   ##
    ####################

    @property
    def is_drawing(self) -> bool:
        """Get the draw state of the Illustrator."""

        return self.__draw

    @is_drawing.setter
    def is_drawing(self, value: bool) -> None:
        """Set the draw state of the Illustrator."""

        # Validate value.
        if not isinstance(value, bool):
            raise TypeError(f"Value must be of type bool, got '{type(value)}'")

        self.__draw = value

    ########################
    ##   PUBLIC METHODS   ##
    ########################

    def draw(self) -> None:
        """Draw the image assets in the game."""

        # Return of drawing is toggled off.
        if not self.__draw:
            return

        self.__draw_background()
        self.__draw_pipes()
        self.__draw_ground()
        self.__draw_birds()

        if (
            self.__game.is_ai
            and len(self.__game.birds)
            and len(self.__game.pipes)
        ):
            self.__draw_guidelines()
            self.__draw_intel()

        if self.__game.state == GameStateEnum.MAIN_MENU:
            self.__draw_main_menu()

        # Draw game over screen.
        elif self.__game.state == GameStateEnum.OVER:
            self.__draw_game_over()

    #########################
    ##   PRIVATE METHODS   ##
    #########################

    def __create_text_sprite(
        self, text: str, size: int
    ) -> tuple[pg.Surface, pg.Rect]:
        """Create a text sprite."""

        font: pg.font.Font = pg.font.SysFont(self.__text_font, size)
        sprite: pg.Surface = font.render(text, True, self.__text_colour)
        return sprite, sprite.get_rect()

    def __draw_background(self) -> None:
        """Draw the background image for the game."""

        background, rect = self.__images["background"]
        self.__game.window.blit(background, rect)

    def __draw_birds(self) -> None:
        """Draw all birds in the game."""

        birds: Iterable[src.objects.bird.Bird] = self.__game.birds
        for bird in birds:
            self.__game.window.blit(bird.image, bird.rect)

    def __draw_game_over(self) -> None:
        """Draw the game over menu."""

        game_over, rect = self.__images["game_over"]
        rect.topleft = get_menu_position(self.__game.window, game_over)
        self.__game.window.blit(game_over, rect)

    def __draw_ground(self) -> None:
        """Draw the game ground menu."""

        ground: src.objects.ground.Ground = self.__game.ground
        self.__game.window.blit(ground.image, ground.rect)

    def __draw_guidelines(self) -> None:
        """Draw AI guidelines per bird."""

        line_color: str = "red"

        # Determine the position of the next obstacle pair.
        top_pipe, btm_pipe = utils.get_next_pipe_pair(
            self.__game.birds[0].rect.x, self.__game.pipes
        )

        for bird in self.__game.birds:
            # Draw gap back.
            pg.draw.line(
                surface=self.__game.window,
                color=line_color,
                start_pos=top_pipe.rect.bottomright,
                end_pos=btm_pipe.rect.topright,
            )

            # Draw line between bird and top pipe.
            pg.draw.line(
                surface=self.__game.window,
                color=line_color,
                start_pos=bird.rect.center,
                end_pos=top_pipe.rect.bottomright,
            )

            # Draw line between bird and bottom pipe.
            pg.draw.line(
                surface=self.__game.window,
                color=line_color,
                start_pos=bird.rect.center,
                end_pos=btm_pipe.rect.topright,
            )

    def __draw_intel(self) -> None:
        """Draw information about the current run."""

        # Update sprites.
        self.__generation_sprite, _ = self.__create_text_sprite(
            str(self.__GENERATION_TEXT.format(self.__game.generation)),
            self.__text_size,
        )

        self.__brood_sprite, _ = self.__create_text_sprite(
            str(self.__BROOD_TEXT.format(len(self.__game.birds))),
            self.__text_size,
        )

        self.__score_sprite, _ = self.__create_text_sprite(
            str(self.__SCORE_TEST.format(self.__game.birds[0].score)),
            self.__text_size,
        )

        self.__time_sprite, _ = self.__create_text_sprite(
            self.__TIME_TEXT.format(
                (get_elapsed_time(time.perf_counter() - self.__start_time))
            ),
            self.__text_size,
        )

        # Draw sprites.
        self.__game.window.blit(
            self.__generation_sprite, self.__generation_rect
        )
        self.__game.window.blit(self.__brood_sprite, self.__brood_rect)
        self.__game.window.blit(self.__score_sprite, self.__score_rect)
        self.__game.window.blit(self.__time_sprite, self.__time_rect)

    def __draw_main_menu(self) -> None:
        """Draw the main menu."""

        main_menu, rect = self.__images["main_menu"]
        rect.topleft = get_menu_position(self.__game.window, main_menu)
        self.__game.window.blit(main_menu, rect)

    def __draw_pipes(self) -> None:
        """Draw all pipes in the game."""

        pipes: Iterable[src.objects.pipe.Pipe] = self.__game.pipes
        for pipe in pipes:
            self.__game.window.blit(pipe.image, pipe.rect)

    def __load_game_over(self) -> tuple[pg.Surface, pg.Rect]:
        """Load the game over screen image."""

        # Get path.
        try:
            sprite_path: str = utils.get_config_value(
                self.__config, "assets.images.menus.game_over"
            )
        except MissingConfigurationError:
            raise

        sprite: pg.Surface = utils.load_asset(sprite_path)
        rect: pg.Rect = sprite.get_rect()

        return sprite, rect

    def __load_background(self, day: bool = True) -> tuple[pg.Surface, pg.Rect]:
        """Load the background image."""

        # Get path.
        try:
            sprite_path: str = utils.get_config_value(
                self.__config,
                "assets.images.background.background_"
                f"{'day' if day else 'night'}",
            )
        except MissingConfigurationError:
            raise

        sprite: pg.Surface = utils.load_asset(sprite_path)
        sprite = pg.transform.scale(
            surface=sprite,
            size=(
                self.__game.window.get_width(),
                self.__game.window.get_height(),
            ),
        )
        rect: pg.Rect = sprite.get_rect()

        return sprite, rect

    def __load_main_menu(self) -> tuple[pg.Surface, pg.Rect]:
        """Load the main menu screen image."""

        # Get path.
        try:
            sprite_path: str = utils.get_config_value(
                self.__config, "assets.images.menus.main_menu"
            )
        except MissingConfigurationError:
            raise

        sprite: pg.Surface = utils.load_asset(sprite_path)
        rect: pg.Rect = sprite.get_rect()

        return sprite, rect


########################
##   FREE FUNCTIONS   ##
########################


def get_elapsed_time(start_time: float) -> datetime.timedelta:
    """Get elapsed time."""

    return datetime.timedelta(seconds=start_time)


def get_menu_position(window: pg.Surface, menu: pg.Surface) -> Position:
    """Get a position for a menu sprite."""

    return (
        (window.get_width() - menu.get_width()) // 2,
        (window.get_height() - menu.get_height()) // 3,
    )
