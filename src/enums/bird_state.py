"""This module contains the BirdStateEnum."""

import enum


class BirdStateEnum(enum.Enum):
    """States that the bird can be in."""

    STANDBY = enum.auto()
    DEAD = enum.auto()
    FLYING = enum.auto()
