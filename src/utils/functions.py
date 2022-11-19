"""This module contains common utility functions for the program."""

from __future__ import annotations

import pathlib

import pygame

from src.utils.types import *


@overload
def load_asset(paths: Iterable[str | pathlib.Path]) -> pygame.Surface:
    ...


@overload
def load_asset(path: str | pathlib.Path) -> Sequence[pygame.Surface]:
    ...


def load_asset(path):
    """Load asset from a file."""

    # Handle a single path.
    if isinstance(path, str | pathlib.Path):

        if isinstance(path, str):
            path = pathlib.Path(path)

        if not path.exists():
            raise FileNotFoundError(f"File {path} not found")

        return pygame.image.load(path)

    # Handle an iterable of paths.
    elif isinstance(path, Iterable):
        paths: list[pathlib.Path] = []

        for p in path:
            if isinstance(p, str):
                p = pathlib.Path(p)

            if not p.exists():
                raise FileNotFoundError(f"File {p} not found")

            paths.append(p)

        return [pygame.image.load(p) for p in paths]

    # Type is not supported.
    else:
        raise TypeError(f"Type {type(path)} not supported for path")


def get_next_obstacle_pair_points(
    x_value: int, obstacles: pg.sprite.AbstractGroup
) -> tuple[pg.sprite.Sprite, pg.sprite.Sprite]:
    """"""

    # Determine the next pair of pipes.
    x_of_next_pair: int = obstacles.sprites()[0].rect.right

    if x_value <= x_of_next_pair:
        top_idx, btm_idx = 0, 1
    else:
        top_idx, btm_idx = 2, 3

    # Get the pipes.
    top_pipe: pg.sprite.Sprite = obstacles.sprites()[top_idx]
    btm_pipe: pg.sprite.Sprite = obstacles.sprites()[btm_idx]

    return top_pipe, btm_pipe
