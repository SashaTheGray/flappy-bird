"""This module contains the Stenographer class.

The Stenographer is a custom logger class extending logging.Logger.

Copyright 2022 Alexander P. Robertson
"""

from __future__ import annotations

import datetime
import enum
import inspect
import logging
import pathlib
import typing


class MessageTypeEnum(enum.Enum):
    """Available Stenographer message types."""

    DEBUG = "[#]"
    INFO = "[i]"
    OPERATION = "[*]"
    SUCCESS = "[+]"
    WARNING = "[!]"
    ERROR = "[-]"
    CRITICAL = "[=]"

    def __str__(self) -> str:
        return f"{self.value}"


class LoggingLevelEnum(enum.IntEnum):
    """Available logging levels."""

    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL

    @classmethod
    def values(cls) -> typing.Iterable[int]:
        """Return all values of the enum."""

        return {key.value for key in cls}


class Stenographer(logging.Logger):
    """Custom logging.Logger class."""

    @classmethod
    def create_logger(
            cls,
            name: str = "",
            *,
            stream_handler: bool = True,
            stream_handler_level: int | str = LoggingLevelEnum.DEBUG,
            file_handler: bool = True,
            file_handler_level: int | str = LoggingLevelEnum.WARNING
    ) -> Stenographer:
        """Create a customized Stenographer instance.

        This instance is highly customized,
        if that is not desired,
        initialize an instance by normal means.

        :param name: Name of the logger.
        :param stream_handler: Should a stream handler be used or not.
        :param file_handler: Should a file handler be used or not.
        :param stream_handler_level: Logging level of the stream handler.
        :param file_handler_level: Logging level of the file handler.
        """

        name = name or _get_caller_module_name()

        # Validate stream handler level.
        if stream_handler:
            if not _validate_logging_level(stream_handler_level):
                raise LookupError(
                    f"{MessageTypeEnum.CRITICAL} Invalid level "
                    f"{stream_handler_level}"
                )

        # Validate file handler level.
        if file_handler:
            if not _validate_logging_level(file_handler_level):
                raise LookupError(
                    f"{MessageTypeEnum.CRITICAL} Invalid level "
                    f"{stream_handler_level}"
                )

        # Create and initialize a stenographer instance.
        stenographer: Stenographer = Stenographer(name)
        fmt: str = _get_message_format(name)
        formatter: logging.Formatter = logging.Formatter(fmt, style="{")

        # Create a stream handler.
        if stream_handler:
            sh: logging.StreamHandler = logging.StreamHandler()
            sh.setFormatter(formatter)
            sh.setLevel(stream_handler_level)
            stenographer.addHandler(sh)

        # Create a file handler.
        if file_handler:
            f: pathlib.Path = _get_log_directory() / _generate_log_file_name()
            fh: logging.FileHandler = logging.FileHandler(f)
            fh.setFormatter(formatter)
            fh.setLevel(file_handler_level)
            stenographer.addHandler(fh)

        return stenographer

    def debug(self, msg: str, **kwargs) -> None:
        msg = f"{MessageTypeEnum.DEBUG} {msg}"
        return super().debug(msg, **kwargs)

    def info(self, msg: str, **kwargs) -> None:
        msg = f"{MessageTypeEnum.INFO} {msg}"
        return super().info(msg, **kwargs)

    def operation(self, msg: str, **kwargs) -> None:
        msg = f"{MessageTypeEnum.OPERATION} {msg}"
        return super().info(msg, **kwargs)

    def success(self, msg: str, **kwargs) -> None:
        msg = f"{MessageTypeEnum.SUCCESS} {msg}"
        return super().info(msg, **kwargs)

    def warning(self, msg: str, **kwargs) -> None:
        msg = f"{MessageTypeEnum.WARNING} {msg}"
        return super().warning(msg, **kwargs)

    def error(self, msg: str, **kwargs) -> None:
        msg = f"{MessageTypeEnum.ERROR} {msg}"
        return super().error(msg, **kwargs)

    def critical(self, msg: str, **kwargs) -> None:
        msg = f"{MessageTypeEnum.CRITICAL} {msg}"
        return super().critical(msg, **kwargs)


def _generate_log_file_name() -> str:
    """Generate a filename for a file stream handler."""

    today: datetime.datetime = datetime.datetime.today()
    return f"{today.year}-{today.month}-{today.day}"


def _get_caller_module_name() -> str:
    """Get the module name of the caller of the previous stack frame."""

    frames: typing.Sequence[inspect.FrameInfo] = inspect.stack()
    skip: int = 2  # Skipping current frame and self.classmethod's frame.
    caller: inspect.FrameInfo = frames[skip]
    return caller.filename.split("\\")[-1]  # Return only the name of the file.


def _get_log_directory(dir: pathlib.Path | None = None) -> pathlib.Path:
    """Get the directory to store log files.

    :param dir: The dir to store the log files.
    """

    if dir is None:
        dir = pathlib.Path().cwd() / "logs"

    if not dir.exists():
        dir.mkdir()

    return dir


def _get_message_format(logger_name: str) -> str:
    """Get message format for a handler.
    :param logger_name: Name of the logger logging the message.
    """

    return (
        "[{asctime}] "
        ":: {levelname:<8} "
        f":: {{name:^20}} "
        ":: {message}"
    )


def _validate_logging_level(lvl: int | str) -> bool:
    """Validate the given logging level."""

    if isinstance(lvl, int):
        return lvl in LoggingLevelEnum.values()
    elif isinstance(lvl, str):
        return lvl.upper() in LoggingLevelEnum
    else:
        return False
