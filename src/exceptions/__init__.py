"""This package contains exceptions for the project."""

from src.exceptions.ai_exceptions import *


class MissingConfigurationError(Exception):
    """Raise when a key is missing from a configuration file."""

    ...
