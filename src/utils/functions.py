"""This module contains common utility functions for the program."""

#################
##   IMPORTS   ##
#################


# Python core imports.
from __future__ import annotations

import pathlib

# Local imports.
from src.exceptions import MissingConfigurationError
from src.utils.types import *

###################
##   CONSTANTS   ##
###################

VOID_CONFIG_ERROR: str = "Config missing for key '{}'"


###################
##   FUNCTIONS   ##
###################


@overload
def load_asset(path: Iterable[str | pathlib.Path]) -> Sequence[pg.Surface]:
    ...


@overload
def load_asset(path: str | pathlib.Path) -> pg.Surface:
    ...


def load_asset(path) -> pg.Surface | Sequence[pg.Surface]:
    """Load asset from a file."""

    # Handle a single path.
    if isinstance(path, str | pathlib.Path):

        if isinstance(path, str):
            path = pathlib.Path(path)

        if not path.exists():
            raise FileNotFoundError(f"File {path} not found")

        return pg.image.load(path)

    # Handle an iterable of paths.
    elif isinstance(path, Iterable):
        paths: list[pathlib.Path] = []

        for p in path:
            if isinstance(p, str):
                p = pathlib.Path(p)

            if not p.exists():
                raise FileNotFoundError(f"File {p} not found")

            paths.append(p)

        return [pg.image.load(p) for p in paths]

    # Type is not supported.
    else:
        raise TypeError(f"Type {type(path)} not supported for path")


def get_config_value(config: Config, key: str, separator: str = ".") -> Any:
    """Get a value from a config object.

    :param config: The game configuration object.
    :param key: Key holding the value to get.
    :param separator: The nested key separator.
    :raises MissingConfigurationError: If configuration os missing.
    """

    try:

        # Get value from config.
        value: Any = config
        for k in key.split(separator):
            value = value.get(k)

        # Value cannot be None.
        if value is None:
            raise AttributeError

        return value

    except (AttributeError, TypeError):
        raise MissingConfigurationError(VOID_CONFIG_ERROR.format(key))


@overload
def get_next_pipe_pair(
    x_value: int, pipes: Sequence[pg.sprite.Sprite]
) -> tuple[pg.sprite.Sprite, pg.sprite.Sprite]:
    ...


def get_next_pipe_pair(
    x_value: int, pipes: pg.sprite.Group
) -> tuple[pg.sprite.Sprite, pg.sprite.Sprite]:
    """Return the next obstacle pair in front of the birds."""

    # Determine the next pair of pipes.
    if isinstance(pipes, pg.sprite.AbstractGroup):
        x_of_next_pair: int = pipes.sprites()[0].rect.right
    elif isinstance(pipes, Sequence):
        x_of_next_pair: int = pipes[0].rect.right
    else:
        raise TypeError(
            "Expected types 'pg.sprite.AbstractGroup' | "
            "'Sequence[pg.sprite.Sprite]' for argument 'pipes', "
            f"got '{type(pipes)}'"
        )

    if x_value <= x_of_next_pair:
        top_idx, btm_idx = 0, 1
    else:
        top_idx, btm_idx = 2, 3

    # Get the pipes.
    if isinstance(pipes, pg.sprite.AbstractGroup):
        top_pipe: pg.sprite.Sprite = pipes.sprites()[top_idx]
        btm_pipe: pg.sprite.Sprite = pipes.sprites()[btm_idx]
    else:

        top_pipe: pg.sprite.Sprite = pipes[top_idx]
        btm_pipe: pg.sprite.Sprite = pipes[btm_idx]

    return top_pipe, btm_pipe
