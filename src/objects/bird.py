"""This module contains the Bird class.

This module includes:
    - Imports
    - Class
"""

#################
##   IMPORTS   ##
#################

from __future__ import annotations

# Local imports.
import src.utils.functions as utils
import src.objects.score_counter
from src.utils.stenographer import Stenographer
from src.enums import BirdStateEnum
from src.utils.types import *

# Pip imports.

if TYPE_CHECKING:
    from pygame import Surface, Rect

LOGGER: Stenographer = Stenographer.create_logger(stream_handler_level=30)


###############
##   CLASS   ##
###############


@final
class Bird(pg.sprite.Sprite):
    """Bird class representing Flappy the Bird."""

    ########################
    ##   DUNDER METHODS   ##
    ########################

    def __init__(
        self, position: Position, config: Config, time_rate: int
    ) -> None:
        """Initialize a Bird instance."""

        LOGGER.operation("Initializing bird")

        # Setup.
        super().__init__()

        self.in_score_zone: bool = False
        self.__time_rate: int = time_rate
        self.__can_fly: bool = True  # Locking system to prevent spamming.
        self.__state: BirdStateEnum = BirdStateEnum.STANDBY
        self.__config: Config = config
        self.__animation_speed: int = config["game"]["animation_speed"]
        self.__velocity: float = config["game"]["velocity"]
        self.__max_velocity: float = config["game"]["max_velocity"]

        # Define the sprites for the bird animation.
        self.__sprites: Sequence[Surface] = utils.load_asset(
            config.get("assets").get("images").get("birds").get("red")
        )
        self.__curr_sprite_idx: int = 0  # Current sprite's index.
        self.__next_sprite_ctr: int = 0  # Counts to animation speed.
        self.__sprite: Surface = self.__sprites[self.__curr_sprite_idx]

        # Position and rect.
        self.__rect: Rect = self.__sprite.get_rect()
        self.__initial_position: Position = position
        self.__rect.center = position

        # Score counter.
        self.__score_counter: src.objects.score_counter.ScoreCounter = (
            src.objects.score_counter.ScoreCounter()
        )

        LOGGER.success("Bird initialized")

    ########################
    ##   PUBLIC METHODS   ##
    ########################

    @property
    def can_fly(self) -> bool:
        """A getter method for attribute 'can_fly'."""

        return self.__can_fly

    @can_fly.setter
    def can_fly(self, value: bool) -> None:
        """A setter method for attribute 'can_fly'."""

        if not isinstance(value, bool):
            raise ValueError(
                f"Unsupported type {type(value)} for argument 'value'"
            )

        self.__can_fly = value

    @property
    def state(self) -> BirdStateEnum:
        """Getter for bird state."""

        return self.__state

    @state.setter
    def state(self, state: BirdStateEnum) -> None:
        """Setter for bird state."""

        if not isinstance(state, BirdStateEnum):
            raise ValueError(
                f"Unsupported type {type(state)} for argument 'state'"
            )

        self.__state = state

    @property
    def image(self) -> Surface:
        return self.__sprite

    @property
    def rect(self) -> Rect:
        return self.__rect

    @property
    def score(self) -> int:
        """Get the score for the bird instance."""

        return self.__score_counter.score

    def increment_score(self) -> None:
        """Increment the birds score."""

        self.__score_counter.increment()

    def reset_score(self) -> None:
        """Reset the scoreboard for this bird."""

        self.__score_counter.reset()

    def draw(self, window: Surface):
        """Draw the bird to the game window."""

        window.blit(self.__sprite, self.__rect)

    def update(self, *args: Any, **kwargs: Any) -> None:
        """On new frame update method."""

        # Return if bird is DEAD.
        if not self.alive:
            return

        self.__handle_velocity()
        self.__handle_animation()

    def fly(self) -> None:
        """Fly."""

        # Bird cannot fly when not flying - "quelle surprise".
        if self.__state != BirdStateEnum.FLYING or not self.__can_fly:
            return

        # Bird cannot fly out of frame.
        if self.__rect[1] < 0:
            return

        # Modify altitude and velocity on fly trigger.
        self.__rect[1] -= self.__config["game"]["jump_height"]
        self.__velocity = self.__config["game"]["jump_velocity_negation"]

    def is_above_ground(self) -> bool:
        """Check whether the bird is above ground."""

        gsth_: float = 0.04  # Ground sprite top height.
        ground: int = self.__config["window"]["height"] * (0.85 - gsth_)
        return self.__rect[1] <= ground

    def reset(self) -> None:
        """Reset the bird."""

        self.__rect.center = self.__initial_position
        self.__can_fly = True
        self.in_score_zone = False
        self.__state = BirdStateEnum.STANDBY
        self.__score_counter.reset()

    #########################
    ##   PRIVATE METHODS   ##
    #########################

    def __set_altitude(self, altitude: float) -> None:
        """Private property setter for self.altitude."""

        self.__rect[1] = altitude

    def __handle_animation(self) -> None:
        """Handle the flying animation."""

        # If bird is killed by ground collision.
        if self.__state == BirdStateEnum.DEAD and not self.is_above_ground():
            # Add pronounced rotation on death.
            self.__sprite = pg.transform.rotate(
                self.__sprites[self.__curr_sprite_idx], -60
            )

            return

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
            self.__velocity * self.__config["game"]["rotation_factor"],
        )

    def __handle_velocity(self) -> None:
        """Handle velocity changes."""

        # Do not change velocity if the bird is not flying.
        if self.__state != BirdStateEnum.FLYING:
            self.__velocity = 0
            return

        # Increment velocity while it's lower than max velocity.
        if self.__velocity < self.__max_velocity:
            self.__velocity += (
                self.__config["game"]["drop_rate"] * self.__time_rate
            )

        # Modify altitude in accordance to current velocity.
        self.__rect[1] += self.__velocity
