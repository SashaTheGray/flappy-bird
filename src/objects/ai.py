"""This module contains the artificial intelligence playing the game."""

from src.utils.types import *


class AI:
    """Crappy Bird artificial intelligence agent."""

    def __init__(self, config: Config) -> None:
        """Initialize an AI instance."""

        self.__config: Config = config
