"""This module contains exception related to the AI."""


class PopulationEmptyError(Exception):
    """Raise when operations are attempted on an empty population."""

    ...


class GenomeDoesNotExistError(Exception):
    """Raise when a genome does not exist."""

    ...


class NetworkDoesNotExistError(Exception):
    """Raise when a genome does not exist."""

    ...
