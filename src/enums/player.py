"""This module contains the PlayerEnum."""

import enum


class PlayerEnum(enum.Enum):
    """Representing entities who can play the game."""

    HUMAN = enum.auto()
    AI = enum.auto()
