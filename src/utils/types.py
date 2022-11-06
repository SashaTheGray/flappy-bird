"""This module contains types for type hinting."""

import pygame as pg

# Import the Python typing library for convenience.
from typing import *
from types import *

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
