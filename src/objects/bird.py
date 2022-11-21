"""This class contains the Bird class.

The class represents our protagonist in the game: Flappy.
"""

#################
##   IMPORTS   ##
#################

# Python core imports.
import math

# Local imports.
import src.objects.score_counter
import src.utils.functions as utils
from src.enums import BirdStateEnum
from src.exceptions import MissingConfigurationError
from src.utils.stenographer import Stenographer
from src.utils.types import *

###################
##   CONSTANTS   ##
###################

LOGGER: Stenographer = Stenographer.create_logger()
VOID_CONFIG_ERROR: str = "Config missing for key '{}'"


###############
##   CLASS   ##
###############


class Bird(pg.sprite.Sprite):
    """Representing a bird in the game."""

    ########################
    ##   DUNDER METHODS   ##
    ########################

    def __init__(self, position: Position, config: Config) -> None:
        """Initialize a Bird instance."""

        super(Bird, self).__init__()

        # Basic state configuration for the bird.
        self.__config: Config = config
        self.__state: BirdStateEnum = BirdStateEnum.STANDBY
        self.__can_fly: bool = True

        # Load the sprites for the bird.
        try:
            self.__sprites: Sequence[pg.Surface] = self.__load_sprites()
        except MissingConfigurationError:
            raise

        # Sprite animation control variables.
        self.__curr_sprite_idx: int = 0
        self.__next_sprite_ctr: int = 0
        self.__sprite: pg.Surface = self.__sprites[self.__curr_sprite_idx]

        # Position.
        self.__rect: pg.Rect = self.__sprite.get_rect()
        self.__rect.center = position
        self.__initial_position: Position = position

        # Score counter.
        self.__score_counter: src.objects.score_counter.ScoreCounter = (
            src.objects.score_counter.ScoreCounter()
        )

        # Flight control variables.
        self.__velocity: float = 0
        self.__max_velocity: float = utils.get_config_value(
            self.__config, "bird.max_velocity"
        )
        self.__animation_speed: int = utils.get_config_value(
            self.__config, "bird.animation_speed"
        )
        self.__drop_rate: float = utils.get_config_value(
            self.__config, "bird.drop_rate"
        )
        self.__jump_height: int = utils.get_config_value(
            self.__config, "bird.jump_height"
        )
        self.__jump_velocity_negation: int = utils.get_config_value(
            self.__config, "bird.jump_velocity_negation"
        )
        self.__rotation_factor: int = utils.get_config_value(
            self.__config, "bird.rotation_factor"
        )

    ####################
    ##   PROPERTIES   ##
    ####################

    @property
    def can_fly(self) -> bool:
        """Get whether the bird can fly or not."""

        return self.__can_fly

    @can_fly.setter
    def can_fly(self, value: bool) -> None:
        """Set whether the bird can fly or not.

        :param value: The new value to set: True/False.
        :raise TypeError: If the value is not of type bool.
        """

        # Validate value.
        if not isinstance(value, bool):
            raise TypeError(f"Value must be of type bool, got '{type(value)}'")

        self.__can_fly = value

    @property
    def state(self) -> BirdStateEnum:
        """Get the state of the bird."""

        return self.__state

    @state.setter
    def state(self, new_state: BirdStateEnum) -> None:
        """Set the state of the bird."""

        # Validate new_state.
        if new_state not in BirdStateEnum:
            raise AttributeError(
                f"BirdStateEnum has not attribute '{new_state}'"
            )

        self.__state = new_state

    @property
    def image(self) -> pg.Surface:
        """Get the PyGame image representing the bird."""

        return self.__sprite

    @property
    def rect(self) -> pg.Rect:
        """Get the rectangle representing the bird's collision box."""

        return self.__rect

    @property
    def score(self) -> int:
        """Get the current score for the bird instance."""

        return self.__score_counter.score

    ########################
    ##   PUBLIC METHODS   ##
    ########################

    def fly(self, speed: float) -> None:
        """Fly the bird."""

        # Bird cannot fly when not flying - "quelle surprise".
        if self.__state != BirdStateEnum.FLYING or not self.__can_fly:
            return

        # Bird cannot fly out of frame.
        if self.__rect[1] < 0:
            return

        # Modify altitude and velocity on fly trigger.
        self.__rect[1] -= math.floor(self.__jump_height * speed)
        self.__velocity = self.__jump_velocity_negation

    def increment_score(self) -> None:
        """Increment the bird's score by 1."""

        self.__score_counter.increment()

    def reset(self) -> None:
        """Reset the bird."""

        self.__rect.center = self.__initial_position
        self.__score_counter.reset()
        self.__state = BirdStateEnum.STANDBY
        self.__can_fly = True

    def update(self, speed: int) -> None:
        """Update the bird instance.

        :param speed: The current game speed.
        """

        # Cannot update the bird if dead.
        if self.__state == BirdStateEnum.DEAD:
            return

        self.__handle_velocity(speed)
        self.__handle_animation()

    #########################
    ##   PRIVATE METHODS   ##
    #########################

    def __handle_animation(self) -> None:
        """Handle the bird animation logic."""

        # On next sprite trigger.
        if self.__next_sprite_ctr >= self.__animation_speed:

            # Update indexer.
            if self.__curr_sprite_idx == len(self.__sprites) - 1:
                self.__curr_sprite_idx = 0
            else:
                self.__curr_sprite_idx += 1

            # Change the sprite and reset next-sprite counter.
            self.__sprite = self.__sprites[self.__curr_sprite_idx]
            self.__next_sprite_ctr = 0

        # Increment trigger counter.
        else:
            self.__next_sprite_ctr += 1

        # Rotate the bird according to its velocity.
        self.__sprite = pg.transform.rotate(
            self.__sprites[self.__curr_sprite_idx],
            self.__velocity * -self.__rotation_factor,
        )

    def __handle_velocity(self, speed: int) -> None:
        """Handle the bird velocity logic.

        :param speed: The current game speed.
        """

        # Disable velocity if the bird is not flying.
        if self.__state != BirdStateEnum.FLYING:
            self.__velocity = 0.0
            return

        # Increment velocity whilst it's lower than max_velocity.
        if self.__velocity < self.__max_velocity:
            self.__velocity += self.__drop_rate * speed

        # Modify altitude in accordance to current velocity.
        self.__rect[1] += math.floor(self.__velocity)

    def __load_sprites(self) -> Sequence[pg.Surface]:
        """Load the sprites for the bird.

        :raises MissingConfigurationError: If image assets cannot be found.
        """

        # Get sprite paths.
        try:
            sprite_paths: Iterable[str] = utils.get_config_value(
                self.__config, "assets.images.birds.red"
            )
        except MissingConfigurationError:
            raise

        else:
            return utils.load_asset(path=sprite_paths)
