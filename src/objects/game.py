"""This module contains the game controller."""

#################
##   IMPORTS   ##
#################

from __future__ import annotations

# Python core imports.
import random

# Local imports.
import src.objects.ai
import src.objects.bird
import src.objects.intel_screen
import src.objects.ground
import src.objects.obstacles
import src.objects.score_counter
import src.utils.functions as utils
from src.enums import BirdStateEnum, PlayerEnum, GameStateEnum
from src.utils.stenographer import Stenographer
from src.utils.types import *

###################
##   CONSTANTS   ##
###################

# The logger instance for this module.
LOGGER: Stenographer = Stenographer.create_logger()

# The action key for the game.
ACTION_KEY: int = pg.K_SPACE

# Pygame tick delay in milliseconds.
DELAY: int = 10


###############
##   CLASS   ##
###############


@final
class Game:
    """Flappy Bird game class."""

    ########################
    ##   DUNDER METHODS   ##
    ########################

    def __init__(
        self, game_config: Config, ai_config: Config | None = None
    ) -> None:
        """Initialize a Game instance.

        :param game_config: Game configurations.
        :param ai_config: AI configurations.
        :raises TypeError: If an invalid type is passed for 'game_config'.
        """

        LOGGER.operation("Initializing game")
        pg.init()

        # Validate game_config.
        if not isinstance(game_config, Mapping):
            raise TypeError(
                f"Unsupported type {type(game_config)} "
                "for argument 'game_config'"
            )

        ####################
        ##   GAME SETUP   ##
        ####################

        # Set the player.
        self.__player: PlayerEnum = (
            PlayerEnum.HUMAN if ai_config is None else PlayerEnum.AI
        )

        # Game configurations.
        self.__config: Config = game_config

        # Game state.
        self.__game_state: GameStateEnum = GameStateEnum.MAIN_MENU

        ######################
        ##   PYGAME SETUP   ##
        ######################

        # Create the game window.
        self.__window: pg.Surface = pg.display.set_mode(
            (
                self.__config["window"]["width"],
                self.__config["window"]["height"],
            )
        )

        # Set a caption for the game window.
        pg.display.set_caption(self.__config["window"]["game_name"])

        # Instantiate a game clock.
        self.__clock: pg.time.Clock = pg.time.Clock()

        # Score counter.
        self.__score_counter: src.objects.score_counter.ScoreCounter = (
            src.objects.score_counter.ScoreCounter(
                (
                    self.__window.get_width() // 2,
                    self.__window.get_height() // 8,
                ),
                self.__config,
            )
        )

        # Create the bird for the game.
        self.__bird: src.objects.bird.Bird = src.objects.bird.Bird(
            (self.__window.get_width() // 5, self.__window.get_height() // 2),
            self.__config,
        )

        # Intelligence.
        self.__intel: src.objects.intel_screen.IntelScreen = (
            src.objects.intel_screen.IntelScreen(
                (self.__bird,), self.__config, text_colour=(0, 0, 0)
            )
        )

        # Has the bird entered the gap between obstacles.
        self.__bird_in_score_zone: bool = False

        # Create the ground for the game.
        self.__ground: src.objects.ground.Ground = src.objects.ground.Ground(
            (0, int(self.__window.get_height() * 0.85)), self, self.__config
        )

        # Create a sprite group for the obstacles in the game.
        self.__obstacles: pg.sprite.AbstractGroup = pg.sprite.Group()

        # Monitor obstacle spawning.
        self.__last_obstacle_spawn_time: float = (
            pg.time.get_ticks()
            - self.__config.get("game").get("obstacle_frequency")
        )

        LOGGER.success("Game initialized")

    def __enter__(self) -> Self:
        """Context manager enter method."""

        return self

    def __exit__(
        self,
        error_type: type | None,
        error: Exception | None,
        traceback: TracebackType | None,
    ) -> None:
        """Context manager exit method."""

        # Handle PyGame exceptions.
        if isinstance(error, pg.error):
            LOGGER.critical(f"Pygame is complaining: {str(error).capitalize()}")

        # Handler other exceptions.
        elif error is not None:
            LOGGER.critical(str(error).capitalize())

        self.__del__()

    def __del__(self) -> None:
        """Game destructor."""

        pg.quit()

    ########################
    ##   PUBLIC METHODS   ##
    ########################

    @property
    def state(self) -> GameStateEnum:
        return self.__game_state

    def play(self) -> None:
        """Play the game."""

        # Game loop.
        keep_playing = True
        while keep_playing:
            # Set delay tick delay.
            pg.time.delay(DELAY)

            # Set frame rate.
            self.__clock.tick(self.__config["game"]["fps"])

            # Control game.
            self.__spawn_obstacle_pair()
            self.__draw_assets()
            self.__handle_flying()
            keep_playing = self.__handle_game_events()
            self.__update()

    #########################
    ##   PRIVATE METHODS   ##
    #########################

    def __spawn_obstacle_pair(self) -> None:
        """Spawn a pair of obstacles in the game."""

        # Return if the spawn interval has not been reached or bird not flying.
        frequency: float = self.__config["game"]["obstacle_frequency"]
        if (
            pg.time.get_ticks() - self.__last_obstacle_spawn_time < frequency
            or not self.__bird.state == BirdStateEnum.FLYING
        ):
            return None

        # Obstacle start position offset from window edge.
        off_screen_offset: int = 10

        # Gap between obstacles.
        obstacle_gap: int = self.__config["game"]["obstacle_gap"] // 2

        # Height offset to randomize heights.
        height_offset: int = random.randint(-100, 100) - obstacle_gap

        # Create the top_obstacle.
        top_obstacle: pg.sprite.Sprite = src.objects.obstacles.Pipe(
            (
                self.__window.get_width() + off_screen_offset,
                (self.__window.get_height() // 2)
                - obstacle_gap
                + height_offset,
            ),
            self.__config,
            reversed_=True,
        )

        # Create the bottom_obstacle.
        bottom_obstacle: pg.sprite.Sprite = src.objects.obstacles.Pipe(
            (
                self.__window.get_width() + off_screen_offset,
                (self.__window.get_height() // 2)
                + obstacle_gap
                + height_offset,
            ),
            self.__config,
            reversed_=False,
        )

        self.__obstacles.add(top_obstacle)
        self.__obstacles.add(bottom_obstacle)

        # Reset spawn interval timer.
        self.__last_obstacle_spawn_time = pg.time.get_ticks()

    def __draw_assets(self) -> None:
        """Draw the game assets to on the window."""

        # Draw the background.
        background: pg.Surface = utils.load_asset(
            self.__config.get("assets")
            .get("images")
            .get("background")
            .get("background_day")
        )
        background = pg.transform.scale(
            surface=background,
            size=(self.__window.get_width(), self.__window.get_height()),
        )
        background_position: Position = (0, 0)
        self.__window.blit(background, background_position)

        # Draw obstacles.
        self.__obstacles.draw(self.__window)

        # Draw ground.
        self.__ground.draw(self.__window)

        # Draw bird.
        self.__bird.draw(self.__window)

        # Draw intel.
        self.__intel.draw(self.__window)

        # Draw the main menu if the games hasn't started.
        if self.__game_state == GameStateEnum.MAIN_MENU:
            main_menu: pg.Surface = utils.load_asset(
                self.__config.get("assets")
                .get("images")
                .get("menus")
                .get("main_menu")
            )
            main_menu_position: Position = get_menu_position(
                self.__window, main_menu
            )
            self.__window.blit(main_menu, main_menu_position)

        # Draw the game over screen if the game is over.
        elif self.__game_state == GameStateEnum.OVER:
            game_over_menu: pg.Surface = utils.load_asset(
                self.__config.get("assets")
                .get("images")
                .get("menus")
                .get("game_over")
            )
            game_over_menu_position: Position = get_menu_position(
                self.__window, game_over_menu
            )
            self.__window.blit(game_over_menu, game_over_menu_position)

    def __handle_collision(self) -> None:
        """Handle object collision in the game."""

        # TODO: Make sure this is still working.
        if not self.__bird.is_above_ground() or pg.sprite.spritecollide(
            self.__bird, self.__obstacles, False
        ):
            self.__game_state = GameStateEnum.OVER
            self.__bird.state = BirdStateEnum.DEAD

    def __handle_flying(self) -> None:
        """Handle bird flying."""

        # Flying occurs only when playing.
        if self.__game_state != GameStateEnum.PLAYING:
            return

        self.__handle_collision()
        self.__handle_scoring()

    def __handle_scoring(self) -> None:
        """Handle the scoring system."""

        # Bird enters score zone.
        if bird_in_score_zone(self.__bird, self.__obstacles):
            self.__bird_in_score_zone = True

        # Bird exits score zone.
        in_zone: bool = bird_in_score_zone(self.__bird, self.__obstacles)
        if self.__bird_in_score_zone and not in_zone:
            self.__score_counter.increment()
            self.__bird_in_score_zone = False

    def __handle_game_events(self) -> bool:
        """Listen for pygame events."""

        keep_playing: bool = True

        for event in pg.event.get():

            # Quit if the player closes the Pygame window.
            if event.type == pg.QUIT:
                keep_playing = False

            # Reset bird when DEAD.
            if (
                self.__bird.state == BirdStateEnum.DEAD
                and self.__game_state == GameStateEnum.OVER
                and action_key_pressed(event)
            ):
                self.__reset()

            # Start flying on STANDBY.
            elif (
                self.__bird.state == BirdStateEnum.STANDBY
                and self.__game_state == GameStateEnum.MAIN_MENU
                and action_key_pressed(event)
            ):
                self.__game_state = GameStateEnum.PLAYING
                self.__bird.state = BirdStateEnum.FLYING
                self.__bird.fly()
                self.__bird.can_fly = False

            # Fly if FLYING.
            elif (
                self.__bird.state == BirdStateEnum.FLYING
                and self.__game_state == GameStateEnum.PLAYING
                and action_key_pressed(event)
            ):
                self.__bird.fly()
                self.__bird.can_fly = False

            # Unlock flying if FLYING.
            elif (
                self.__bird.state == BirdStateEnum.FLYING
                and self.__game_state == GameStateEnum.PLAYING
                and action_key_released(event)
            ):
                self.__bird.can_fly = True

        return keep_playing

    def __reset(self) -> None:
        """Reset the game."""

        # Reset bird.
        self.__bird.reset()
        self.__bird_in_score_zone = False

        # Delete all obstacles.
        self.__obstacles.empty()

        # Reset score counter.
        self.__score_counter.reset()

        # Set game state to main menu.
        self.__game_state = GameStateEnum.MAIN_MENU

    def __update(self) -> None:
        """Update the game."""

        # Update the obstacles if the bird is flying.
        if self.__bird.state == BirdStateEnum.FLYING:
            self.__obstacles.update()

        # Update the ground whilst the game is not over.
        if self.__game_state != GameStateEnum.OVER:
            self.__ground.update()

        # Update the bird.
        self.__bird.update()

        # Update intel.
        x, y = get_distance(self.__bird, self.__obstacles)
        self.__intel.update(self.__score_counter.score, x, y)

        # Update the game window.
        pg.display.update()


########################
##   FREE FUNCTIONS   ##
########################


def action_key_pressed(event: pg.event.Event) -> bool:
    """Was the action key pressed.

    :param event: An active PyGame event.
    :raises TypeError: If event type is not supported.
    """

    # Validate argument.
    if not isinstance(event, pg.event.Event):
        raise TypeError(f"Unsupported type {type(event)} for argument 'event'")

    return event.type == pg.KEYDOWN and event.key == ACTION_KEY


def action_key_released(event: pg.event.Event) -> bool:
    """Was the action key released.

    :param event: An active PyGame event.
    :raises TypeError: If event type is not supported.
    """

    # Validate argument.
    if not isinstance(event, pg.event.Event):
        raise TypeError(f"Unsupported type {type(event)} for argument 'event'")

    return event.type == pg.KEYUP and event.key == ACTION_KEY


def bird_in_score_zone(
    bird: src.objects.bird.Bird, obstacles: pg.sprite.AbstractGroup
) -> bool:
    """Check if the bird is flying through the gap between obstacles.

    :param bird: A Bird instance.
    :param obstacles: The group of active obstacles within the game.
    :raises TypeError: If provided arguments are of unsupported type.
    """

    # Validate bird argument.
    if not isinstance(bird, src.objects.bird.Bird):
        raise TypeError(f"Unsupported type {type(bird)} for argument 'bird'")

    # Validate obstacles argument.
    elif not isinstance(obstacles, pg.sprite.AbstractGroup):
        raise TypeError(
            f"Unsupported type {type(obstacles)} for argument 'obstacles'"
        )

    # If there are no obstacles present.
    if not len(obstacles):
        return False

    # Return check.
    return (
        bird.rect.right > obstacles.sprites()[0].rect.left
        and bird.rect.left < obstacles.sprites()[0].rect.right
    )


def get_distance(
    bird: src.objects.bird.Bird, obstacles: pg.sprite.AbstractGroup
) -> Position:
    """Get the distance between the bird and the next obstacle."""

    # TODO: Implement.
    return 0, 0


def get_menu_position(window: pg.Surface, menu: pg.Surface) -> Position:
    """Get a position for a menu sprite."""

    return (
        (window.get_width() - menu.get_width()) // 2,
        (window.get_height() - menu.get_height()) // 3,
    )
