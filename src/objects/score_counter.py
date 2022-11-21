"""This module contains the ScoreCounter class.

ScoreCounter maintains the total score for birds.
"""


#################
##   IMPORTS   ##
#################

###################
##   CONSTANTS   ##
###################


class ScoreCounter:
    """"""

    ########################
    ##   DUNDER METHODS   ##
    ########################

    def __init__(self):
        self.__score: int = 0

    ####################
    ##   PROPERTIES   ##
    ####################

    @property
    def score(self) -> int:
        """Get the current score."""

        return self.__score

    ########################
    ##   PUBLIC METHODS   ##
    ########################

    def increment(self) -> None:
        """Increment the current score by 1."""

        self.__score += 1

    def reset(self) -> None:
        """Reset the instance."""

        self.__score = 0

    #########################
    ##   PRIVATE METHODS   ##
    #########################
