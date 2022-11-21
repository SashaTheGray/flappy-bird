"""This module contains types for type hinting."""

import pygame as pg
import neat

# Import the Python typing library for convenience.
from typing import (
    Iterator,
    Iterable,
    Sequence,
    final,
    overload,
    Any,
    TYPE_CHECKING,
    Callable,
    BinaryIO
)

__all__ = [
    "Config",
    "Position",
    "Drawable",
    "RGB",
    "Genotype",
    "Phenotype",
    "Iterator",
    "Iterable",
    "Sequence",
    "final",
    "overload",
    "pg",
    "neat",
    "Any",
    "TYPE_CHECKING",
    "Callable",
    "BinaryIO"
]

# Type aliases.
__AI_CONFIG = dict[str, float]
__GAME_CONFIG = dict[str, str | int | float]

Config = __AI_CONFIG | __GAME_CONFIG
Position = tuple[int, int]
Drawable = (
    tuple[pg.sprite.AbstractGroup, Position]
    | tuple[pg.Surface, Position]
    | tuple[str, Position]
)

RGB = tuple[int, int, int]
Genotype = neat.DefaultGenome
Phenotype = neat.nn.FeedForwardNetwork
