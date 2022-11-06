"""This module contains the GameStateEnum."""

import enum


class GameStateEnum(enum.Enum):
    """Possible game states."""

    MAIN_MENU = enum.auto()
    PLAYING = enum.auto()
    OVER = enum.auto()
