"""This module contains the game controller."""

#################
##   IMPORTS   ##
#################

from __future__ import annotations

# Python core imports.
import math
import random

# Local imports.
import src.objects.ai
import src.objects.bird
import src.objects.ground
import src.objects.intel_screen
import src.objects.obstacles
import src.objects.score_counter
import src.utils.functions as utils
from src.enums import BirdStateEnum, GameStateEnum
from src.utils.stenographer import Stenographer
from src.utils.types import *

# Pip imports.

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

    # noinspection PyTypeChecker
    def __init__(
        self, game_config: Config, ai: src.objects.ai.AI | None = None
    ) -> None:
        """Initialize a Game instance."""

        LOGGER.operation("Initializing game")
        pg.init()

        # Validate game_config.
        if not isinstance(game_config, Mapping):
            raise TypeError(
                f"Unsupported type {type(game_config)} "
                "for argument 'game_config'"
            )

        # AI setup.
        self.__is_ai: bool = ai is not None
        self.__ai: src.objects.ai.AI | None = ai

        # Game setup.
        self.__config: Config = game_config
        self.__game_state: GameStateEnum = GameStateEnum.MAIN_MENU
        self.__window: pg.Surface = pg.display.set_mode(
            (
                self.__config["window"]["width"],
                self.__config["window"]["height"],
            )
        )
        pg.display.set_caption(self.__config["window"]["game_name"])
        self.__clock: pg.time.Clock = pg.time.Clock()
        self.__birds: pg.sprite.AbstractGroup = pg.sprite.AbstractGroup()
        self.__ground_group: pg.sprite.AbstractGroup = pg.sprite.AbstractGroup()
        self.__ground: src.objects.ground.Ground = src.objects.ground.Ground(
            (0, int(self.__window.get_height() * 0.85)), self, self.__config
        )
        self.__ground_group.add(self.__ground)
        self.__intel: src.objects.intel_screen.IntelScreen = (
            src.objects.intel_screen.IntelScreen(
                self.__config, text_colour=(0, 0, 0)
            )
        )
        self.__obstacles: pg.sprite.AbstractGroup = pg.sprite.Group()
        self.__last_obstacle_spawn_time: float = (
            pg.time.get_ticks()
            - self.__config.get("game").get("obstacle_frequency")
        )

        LOGGER.success("Game initialized")

    ########################
    ##   PUBLIC METHODS   ##
    ########################

    @property
    def state(self) -> GameStateEnum:
        return self.__game_state

    @state.setter
    def state(self, state: GameStateEnum) -> None:
        # TODO: Validate state.
        self.__game_state = state

    # noinspection PyTypeChecker
    def add_bird(self, amount: int = 1) -> None:
        """Add a bird to the game."""

        for _ in range(amount):
            bird: src.objects.bird.Bird = src.objects.bird.Bird(
                position=(
                    self.__window.get_width() // 5,
                    self.__window.get_height() // 2,
                ),
                config=self.__config,
            )

            self.__birds.add(bird)

        LOGGER.debug(f"Added {amount:,} birds to game")

    def play(self) -> None:
        """Play the game as human."""

        if not self.__is_ai:
            self.add_bird()

        # Game loop.
        keep_playing = True
        while keep_playing:

            if not len(self.__birds):
                break

            # Set delay tick delay.
            pg.time.delay(DELAY)

            # Set frame rate.
            self.__clock.tick(self.__config["game"]["fps"])

            # Control game.
            self.__spawn_obstacle_pair()
            self.__draw_assets()

            # Bird controllers.
            if self.__is_ai and len(self.__obstacles):
                self.__to_fly_or_not_to_fly()

            # Handle collision and scoring if the game is playing.
            if self.__game_state == GameStateEnum.PLAYING:
                self.__handle_collision()
                self.__handle_scoring()

            # Handle game events and update the game.
            keep_playing = self.__handle_game_events()
            self.__update()

        # Enforce the game to restart for when the AI is playing.
        if self.__is_ai and keep_playing:
            return self.__reset()
        else:
            pg.quit()

    #########################
    ##   PRIVATE METHODS   ##
    #########################

    def __to_fly_or_not_to_fly(self) -> None:

        # Pass each bird through its phenotype.
        for idx, bird in enumerate(self.__birds):

            # Enable the bird to fly.
            bird.can_fly = True
            bird.state = BirdStateEnum.FLYING

            # Observe input parameters.
            altitude: float = bird.rect.y
            btm_pipe_delta, top_pipe_delta = get_pipe_deltas(
                bird, self.__obstacles
            )

            if self.__ai.should_fly(
                genome_id=idx,
                input_parameters=(altitude, top_pipe_delta, btm_pipe_delta),
            ):
                bird.fly()

    # noinspection PyTypeChecker
    def __spawn_obstacle_pair(self) -> None:
        """Spawn a pair of obstacles in the game."""

        # Return if the spawn interval has not been reached or bird not flying.
        if (
            pg.time.get_ticks() - self.__last_obstacle_spawn_time
            < self.__config["game"]["obstacle_frequency"]
            or self.__game_state != GameStateEnum.PLAYING
        ):
            return

        # Obstacle starting position offset from window edge.
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

        # Reward all birds alive if they are alive at this point.
        if self.__is_ai:
            for idx in range(len(self.__birds)):
                self.__ai.reward(idx, 10)

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
        self.__birds.draw(self.__window)

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

    # noinspection PyTypeChecker
    def __handle_collision(self) -> None:
        """Handle object collision in the game."""

        idx: int = 0
        for bird in self.__birds:

            # Penalize bird for flying to the top.
            if (
                bird.rect.y <= 0
                and self.__game_state == GameStateEnum.PLAYING
                and self.__is_ai
            ):
                self.__ai.penalize(idx)

            # Check for ground collision.
            ground_collision: bool = pg.sprite.spritecollide(
                bird, self.__ground_group, False
            )

            # Check for obstacle collision.
            obstacle_collision: bool = pg.sprite.spritecollide(
                bird, self.__obstacles, False
            )

            # Continue if there is no collision.
            if not ground_collision and not obstacle_collision:
                idx += 1
                continue

            # Only applicable for AI.
            elif self.__is_ai:

                # Penalize the genome for causing a collision.
                self.__ai.penalize(idx)

                # Remove bird's pheno- and genotype from current generation.
                self.__ai.remove(idx)

                # Remove the bird from birds in current generation.
                self.__birds.remove(bird)

            # Only applicable for humans, set game state and kill the bird.
            else:
                self.__game_state = GameStateEnum.OVER
                self.__birds.sprites()[0].state = BirdStateEnum.DEAD

    def __handle_scoring(self) -> None:
        """Handle the scoring system."""

        for idx, bird in enumerate(self.__birds):

            # Bird enters score zone.
            if bird_in_score_zone(bird, self.__obstacles):
                bird.in_score_zone = True

                # Reward the bird for reaching the score zone.
                if self.__is_ai:
                    self.__ai.reward(idx)

            # Bird exits score zone.
            in_zone: bool = bird_in_score_zone(bird, self.__obstacles)
            if bird.in_score_zone and not in_zone:

                # Reward the bird for exiting the score zone.
                if self.__is_ai:
                    self.__ai.reward(idx)

                # Increment score and mark bird as out of zone.
                bird.increment_score()
                bird.in_score_zone = False

    def __handle_game_events(self) -> bool:
        """Listen for pygame events."""

        keep_playing: bool = True

        for event in pg.event.get():

            # Quit if the player closes the Pygame window.
            if event.type == pg.QUIT:
                return False

            # None of the other events are relevant if the AI is playing.
            elif self.__is_ai:
                return True

            bird: src.objects.bird.Bird = self.__birds.sprites()[0]

            # Reset bird when DEAD.
            if (
                bird.state == BirdStateEnum.DEAD
                and self.__game_state == GameStateEnum.OVER
                and action_key_pressed(event)
            ):
                self.__reset()

            # Start flying on STANDBY.
            elif (
                bird.state == BirdStateEnum.STANDBY
                and self.__game_state == GameStateEnum.MAIN_MENU
                and action_key_pressed(event)
            ):
                self.__game_state = GameStateEnum.PLAYING
                bird.state = BirdStateEnum.FLYING
                bird.fly()
                bird.can_fly = False

            # Fly if FLYING.
            elif (
                bird.state == BirdStateEnum.FLYING
                and self.__game_state == GameStateEnum.PLAYING
                and action_key_pressed(event)
            ):
                bird.fly()
                bird.can_fly = False

            # Unlock flying if FLYING.
            elif (
                bird.state == BirdStateEnum.FLYING
                and self.__game_state == GameStateEnum.PLAYING
                and action_key_released(event)
            ):
                bird.can_fly = True

        return keep_playing

    def __reset(self) -> None:
        """Reset the game."""

        # Reset birds.
        if self.__is_ai:
            self.__birds.empty()
        else:
            for bird in self.__birds:
                bird.reset()

        # Delete all obstacles.
        self.__obstacles.empty()

        # Set game state to main menu.
        self.__game_state = GameStateEnum.MAIN_MENU

    def __update(self) -> None:
        """Update the game."""

        # Update the obstacles if the birds are flying.
        if self.__game_state == GameStateEnum.PLAYING:
            self.__obstacles.update()

        # Update the ground whilst the game is not over.
        if self.__game_state != GameStateEnum.OVER:
            self.__ground.update()

        # Update the birds.
        self.__birds.update()

        # Update intel.
        self.__intel.update(
            None if not len(self.__birds) else self.__birds.sprites()[0].score
        )

        # Update the game window.
        pg.display.update()
        pg.display.flip()


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

    # Return the check result.
    return (
        bird.rect.right > obstacles.sprites()[0].rect.left
        and bird.rect.left < obstacles.sprites()[0].rect.right
    )


def get_menu_position(window: pg.Surface, menu: pg.Surface) -> Position:
    """Get a position for a menu sprite."""

    return (
        (window.get_width() - menu.get_width()) // 2,
        (window.get_height() - menu.get_height()) // 3,
    )


def get_pipe_deltas(
    bird: src.objects.bird.Bird, obstacles: pg.sprite.AbstractGroup
) -> tuple[float, float]:
    """Get the distance from the bird to the start of the next obstacle gap."""

    bird_x: int = bird.rect.x
    x_of_next_pair: float = obstacles.sprites()[0].rect.x
    btm_idx, top_idx = (0, 1) if bird_x < x_of_next_pair else (2, 3)

    # Get the pipes.
    btm_pipe: src.objects.obstacles = obstacles.sprites()[btm_idx]
    top_pipe: src.objects.obstacles = obstacles.sprites()[top_idx]

    # Get the corner positions.
    btm_pipe_point: Position = btm_pipe.rect.topleft
    top_pipe_point: Position = top_pipe.rect.topright

    # Return the distance measurements: bird -> btm_pipe, bird -> top_pipe.
    return (
        get_distance(bird.rect.center, btm_pipe_point),
        get_distance(bird.rect.center, top_pipe_point),
    )


def get_distance(point_1: Position, point_2: Position) -> float:
    """Get the distance between the two points."""

    return math.dist(point_1, point_2)
