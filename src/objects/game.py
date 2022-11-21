"""This module contains the game class.

It represents the game and is the main controller for Flappy Bird.
"""

#################
##   IMPORTS   ##
#################

from __future__ import annotations

# Python core imports.
import random

# Local imports.
import src.objects.bird
import src.objects.ground
import src.objects.illustrator
import src.objects.pipe
import src.objects.speedometer
import src.utils.functions as utils
from src.enums import GameStateEnum, BirdStateEnum
from src.exceptions import MissingConfigurationError
from src.utils.stenographer import Stenographer
from src.utils.types import *

if TYPE_CHECKING:
    import src.objects.ai

###################
##   CONSTANTS   ##
###################

LOGGER: Stenographer = Stenographer.create_logger()
ACTION_KEY: int = pg.K_SPACE


###############
##   CLASS   ##
###############


@final
class Game:
    """The game controller for this project."""

    ########################
    ##   DUNDER METHODS   ##
    ########################

    def __init__(
        self, game_config: Config, ai: src.objects.ai.NeatAITrain | None = None
    ) -> None:
        """Initialize a Game instance.

        :param game_config: The game configurations.
        :param ai: Instance of a NEAT-AI class.
        """

        LOGGER.operation("Initializing Game instance")

        pg.init()

        self.__config: Config = game_config
        self.__ai: src.objects.ai.NeatAITrain | None = ai
        self.__is_ai: bool = self.__ai is not None
        self.__random_generator: random.Random = random.Random()
        self.__state: GameStateEnum = GameStateEnum.MAIN_MENU
        self.__window: pg.Surface = self.__init__window()
        self.__clock: pg.time.Clock = pg.time.Clock()
        self.__illustrator: src.objects.illustrator.Illustrator = (
            src.objects.illustrator.Illustrator(config=self.__config, game=self)
        )
        self.__speedometer: src.objects.speedometer.Speedometer = (
            src.objects.speedometer.Speedometer(self.__config)
        )

        self.__score_zone: set[int] = set()
        self.__birds: pg.sprite.Group = pg.sprite.Group()
        self.__ground: pg.sprite.Group = self.__init__ground()
        self.__pipes: pg.sprite.Group = pg.sprite.Group()

        # Pipe spawn control variables.
        self.__last_obstacle_spawn_frame: int = 0

        self.__spawn_frequency: int = utils.get_config_value(
            self.__config, "pipe.spawn_frequency"
        )
        self.__obstacle_gap: int = utils.get_config_value(
            self.__config, "pipe.pipe_gap"
        )
        self.__off_screen_spawn_offset: int = utils.get_config_value(
            self.__config, "pipe.off_screen_offset"
        )
        self.__gap_offset: int = utils.get_config_value(
            self.__config, "pipe.pipe_gap_offset"
        )
        self.__fps: int = utils.get_config_value(self.__config, "game.fps")

        # Update control variables.
        self.__frame_counter: int = 0

        LOGGER.success("Game instance initialized")

    ####################
    ##   PROPERTIES   ##
    ####################

    @property
    def birds(self) -> Sequence[src.objects.bird.Bird]:
        """Get the birds in the game."""

        return self.__birds.sprites()

    @property
    def generation(self) -> int | None:
        """Get the current generation."""

        if self.__is_ai:
            return self.__ai.generation
        return None

    @property
    def ground(self) -> src.objects.ground.Ground:
        """Get the ground of the game."""

        return self.__ground.sprites().pop()

    @property
    def is_ai(self) -> bool:
        """Get whether the AI is active or not."""

        return self.__is_ai

    @property
    def pipes(self) -> Sequence[src.objects.pipe.Pipe]:
        """Get the pipes in the game."""

        return self.__pipes.sprites()

    @property
    def state(self) -> GameStateEnum:
        """Get the state of the game."""

        return self.__state

    @property
    def window(self) -> pg.Surface:
        """Get the game window."""

        return self.__window

    ########################
    ##   PUBLIC METHODS   ##
    ########################

    def play(self, random_seed: int | None = None) -> None:
        """Play the game.

        :param random_seed: Random seed for pipe spawning.
        """

        # Set random seed if present.
        if random_seed is not None:
            self.__random_generator.seed(random_seed)

        if self.__is_ai:
            self.__state = GameStateEnum.PLAYING

        # Add birds to the game.
        self.__add_bird(amount=1 if not self.__is_ai else len(self.__ai))

        # Game loop.
        keep_playing: bool = True
        while keep_playing:

            self.__clock.tick(self.__fps)

            # Listen for game events -> therein human bird controller.
            keep_playing = self.__handle_game_events()

            # Spawn pipes.
            self.__spawn_pipes()

            # Handle collision and scoring if the game is playing.
            if self.__state == GameStateEnum.PLAYING:
                self.__handle_collision()
                self.__handle_scoring()

            # AI bird controller.
            if self.__is_ai and len(self.__pipes):
                self.__to_fly_or_not_to_fly()

            # Update the game.
            if keep_playing:
                self.__update()
                self.__illustrator.draw()

            # If there are no birds left the game is over.
            if not len(self.__birds):
                keep_playing = False

            # Reward birds for being alive.
            if self.__is_ai:
                for idx in range(len(self.__ai)):
                    self.__ai.reward(idx, 0.15)

            self.__update()
            self.__frame_counter += 1

        # Quit the game if human is playing or AI is testing.
        if not self.__is_ai or self.__ai.should_quit():
            return pg.quit()

        self.__reset()

    #########################
    ##   PRIVATE METHODS   ##
    #########################

    def __add_bird(self, amount: int = 1) -> None:
        """Add a bird to the game.

        :param amount: The amount of birds to add.
        :raises TypeError: If amount is not an integer.
        :raises ValueError: If amount is not a positive integer.
        """

        LOGGER.operation(
            f"Adding {amount} {'bird' if amount == 1 else 'birds'}"
        )

        # Validate amount type.
        if not isinstance(amount, int):
            raise TypeError(
                f"Amount must be of type integer, got '{type(amount)}'"
            )

        # Validate amount value.
        if amount <= 0:
            raise ValueError(
                f"Amount must be a positive integer, got '{amount:,}'"
            )

        # Set initial spawn position.
        x = self.__window.get_width() // 5
        y = self.__window.get_height() // 2

        for _ in range(amount):
            new_bird: src.objects.bird.Bird = src.objects.bird.Bird(
                position=(x, y), config=self.__config
            )

            # Ignore type checker, PyGame is not using type hinting correctly.
            # noinspection PyTypeChecker
            self.__birds.add(new_bird)

        LOGGER.success("Birds added")

    def __handle_collision(self) -> None:
        """Handle object collision."""

        idx: int = 0
        for bird in self.__birds:

            # Penalize bird for flying to the top.
            if bird.rect.y <= 0 and self.__is_ai:
                self.__ai.penalize(idx)

            # Check for ground collision.
            # Ignore type checker, PyGame is not using type hinting correctly.
            # noinspection PyTypeChecker
            ground_collision: bool = pg.sprite.spritecollide(
                bird, self.__ground, False
            )

            # Check for obstacle collision.
            # Ignore type checker, PyGame is not using type hinting correctly.
            # noinspection PyTypeChecker
            obstacle_collision: bool = pg.sprite.spritecollide(
                bird, self.__pipes, False
            )

            # Continue if there is no collision.
            if not ground_collision and not obstacle_collision:
                idx += 1
                continue

            # Only applicable for AI.
            elif self.__is_ai:

                # Penalize the genome for causing a collision.
                if ground_collision:
                    self.__ai.penalize(idx)

                # Remove bird's pheno- and genotype from current generation.
                self.__ai.remove(idx)
                self.__birds.remove(bird)

            # Only applicable for humans, set game state and kill the bird.
            else:
                self.__state = GameStateEnum.OVER
                bird.state = BirdStateEnum.DEAD

    def __handle_game_events(self) -> bool:
        """Handle events through the PyGame event listener."""

        for event in pg.event.get():

            # Quit if the player closes the Pygame window.
            if event.type == pg.QUIT or event.type == pg.WINDOWCLOSE:

                if self.__is_ai:
                    self.__ai.quit_early()

                return False

            if self.__is_ai:
                return True

            bird: src.objects.bird.Bird = self.__birds.sprites()[0]

            # Reset bird when DEAD.
            if (
                bird.state == BirdStateEnum.DEAD
                and self.__state == GameStateEnum.OVER
                and action_key_pressed(event)
            ):
                self.__reset()

            # Start flying on STANDBY.
            elif (
                bird.state == BirdStateEnum.STANDBY
                and self.__state == GameStateEnum.MAIN_MENU
                and action_key_pressed(event)
            ):
                self.__state = GameStateEnum.PLAYING
                bird.state = BirdStateEnum.FLYING
                bird.fly(self.__speedometer.speed)
                bird.can_fly = False

            # Fly if FLYING.
            elif (
                bird.state == BirdStateEnum.FLYING
                and self.__state == GameStateEnum.PLAYING
                and action_key_pressed(event)
            ):
                bird.fly(self.__speedometer.speed)
                bird.can_fly = False

            # Unlock flying if FLYING.
            elif (
                bird.state == BirdStateEnum.FLYING
                and self.__state == GameStateEnum.PLAYING
                and action_key_released(event)
            ):
                bird.can_fly = True

        pg.event.clear()
        return True

    def __handle_scoring(self) -> None:
        """Handle bird scoring."""

        for idx, bird in enumerate(self.__birds):

            # Bird enters score zone.
            if bird_in_score_zone(bird, self.__pipes):
                self.__score_zone.add(idx)

                # Reward the bird for reaching the score zone.
                if self.__is_ai:
                    self.__ai.reward(idx)

            # Bird exits score zone.
            in_zone: bool = bird_in_score_zone(bird, self.__pipes)
            if idx in self.__score_zone and not in_zone:

                # Reward the bird for exiting the score zone.
                if self.__is_ai:
                    self.__ai.reward(idx)

                # Increment score and mark bird as out of zone.
                bird.increment_score()
                self.__score_zone.remove(idx)

    def __init__ground(self) -> pg.sprite.Group:
        """Initialize a Ground instance and add it to a sprite group."""

        ground: src.objects.ground.Ground = src.objects.ground.Ground(
            self, self.__config
        )
        group: pg.sprite.Group = pg.sprite.Group()

        # Ignore type checker, PyGame is not using type hinting correctly.
        # noinspection PyTypeChecker
        group.add(ground)
        return group

    def __init__window(self) -> pg.Surface:
        """Initialize the game window."""

        # Get dimensions.
        try:
            width = utils.get_config_value(self.__config, "game.window_width")
            height = utils.get_config_value(self.__config, "game.window_height")
        except MissingConfigurationError:
            raise

        window: pg.Surface = pg.display.set_mode((width, height))

        # Get game name:
        try:
            game_name: str = utils.get_config_value(
                self.__config, "game.game_name"
            )
        except MissingConfigurationError:
            game_name = "Flappy Bird"

        pg.display.set_caption(game_name)
        return window

    def __reset(self) -> None:
        """Reset the game."""

        # Reset birds.
        if self.__is_ai:
            self.__birds.empty()
        else:
            for bird in self.__birds:
                bird.reset()

        # Delete all obstacles.
        self.__pipes.empty()

        # Set game state to main menu.
        self.__state = GameStateEnum.MAIN_MENU

        # Reset control variables.
        self.__last_obstacle_spawn_frame = 0
        self.__frame_counter = 0

    def __spawn_pipes(self) -> None:
        """Spawn a pair of pipes into the game."""

        # No pipe spawning if the game is not playing.
        if self.__state != GameStateEnum.PLAYING:
            return

        # No pipe spawning if spawn interval has not been reached.
        elif self.__frame_counter - self.__last_obstacle_spawn_frame < (
            self.__spawn_frequency // self.__speedometer.speed
        ):
            return

        # Randomize gap heights.
        height_offset: int = self.__random_generator.randint(
            -self.__gap_offset, self.__gap_offset
        )

        # Create the top pipe.
        top_pipe: src.objects.pipe.Pipe = src.objects.pipe.Pipe(
            position=(
                self.__window.get_width() + self.__off_screen_spawn_offset,
                (self.__window.get_height() // 2)
                - self.__obstacle_gap // 2
                + height_offset,
            ),
            config=self.__config,
            reversed=True,
        )

        # Create the top pipe.
        btm_pipe: src.objects.pipe.Pipe = src.objects.pipe.Pipe(
            position=(
                self.__window.get_width() + self.__off_screen_spawn_offset,
                (self.__window.get_height() // 2)
                + self.__obstacle_gap
                + height_offset,
            ),
            config=self.__config,
            reversed=False,
        )

        # Ignore type checker, PyGame is not using type hinting correctly.
        # noinspection PyTypeChecker
        self.__pipes.add(top_pipe)
        # noinspection PyTypeChecker
        self.__pipes.add(btm_pipe)

        # Reset spawn interval timer.
        self.__last_obstacle_spawn_frame = self.__frame_counter

    def __to_fly_or_not_to_fly(self) -> None:
        """For each bird, determine whether it should fly and if so; do so."""

        # Pass each bird through its phenotype.
        for idx, bird in enumerate(self.__birds):

            # Enable the bird to fly.
            bird.can_fly = True
            bird.state = BirdStateEnum.FLYING

            # Observe input parameters.
            top_pipe, btm_pipe = utils.get_next_pipe_pair(
                bird.rect.x, self.__pipes
            )

            # Calculate input parameters.
            delta_y_to_top: float = bird.rect.y - top_pipe.rect.bottomright[1]
            delta_y_to_btm: float = bird.rect.y - btm_pipe.rect.topright[1]
            delta_x: float = btm_pipe.rect.topright[0] - bird.rect.x

            if self.__ai.should_fly(
                genome_id=idx,
                input_parameters=(delta_x, delta_y_to_top, delta_y_to_btm),
            ):
                bird.fly(self.__speedometer.speed)

    def __update(self) -> None:
        """Update the game."""

        # Update the obstacles if the birds are flying.
        if self.__state == GameStateEnum.PLAYING:
            self.__pipes.update(self.__speedometer.speed)

        # Update the ground whilst the game is not over.
        if self.__state != GameStateEnum.OVER:
            self.__ground.update(self.__speedometer.speed)

        # Update the birds.
        self.__birds.update(self.__speedometer.speed)

        # Update the game window.
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
    bird: src.objects.bird.Bird, pipes: pg.sprite.Group
) -> bool:
    """Check if the bird is flying through the gap between obstacles.

    :param bird: A Bird instance.
    :param pipes: The group of active pipes within the game.
    :raises TypeError: If provided arguments are of unsupported type.
    """

    # Validate bird argument.
    if not isinstance(bird, src.objects.bird.Bird):
        raise TypeError(f"Unsupported type {type(bird)} for argument 'bird'")

    # Validate pipes argument.
    elif not isinstance(pipes, pg.sprite.Group):
        raise TypeError(
            f"Unsupported type {type(pipes)} for argument 'obstacles'"
        )

    # If there are no obstacles present.
    if not len(pipes):
        return False

    # Return the check result.
    return (
        bird.rect.right > pipes.sprites()[0].rect.left
        and bird.rect.left < pipes.sprites()[0].rect.right
    )
