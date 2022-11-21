"""This module contains the NeatAITrain class.

Representing the NeuroEvolution of Augmented Topologies Artificial Intelligence
that will be trained- and tested on the game.
"""

#################
##   IMPORTS   ##
#################

# Python core imports.
import abc
import pathlib
import pickle

# Local imports.
import src.objects.game
import src.utils.functions as utils
from src.exceptions import (
    PopulationEmptyError,
    GenomeDoesNotExistError,
    NetworkDoesNotExistError,
)
from src.utils.stenographer import Stenographer
from src.utils.types import *

# Pip imports.

###################
##   CONSTANTS   ##
###################

LOGGER: Stenographer = Stenographer.create_logger()
POPULATION_EMPTY_ERROR: str = "Population is empty"
VOID_GENOME_ERROR: str = "Genome with id '{}' does not exist"
VOID_NETWORK_ERROR: str = "Network with id '{}' does not exist"
VOID_CONFIG_ERROR: str = "Config missing for key '{}'"


#################
##   CLASSES   ##
#################


class ABCNeatAI(abc.ABC):
    """Abstract base class for AIs."""

    # Path to the NEAT configurations file.
    __CONFIG_PATH: str = "src/config/ai_config.cfg"

    def __init__(self, config: Config) -> None:
        self._game_config: Config = config
        self._neat_config: neat.Config = self.__load_config()
        self._population = None
        self._active_phenotypes = None

    def __len__(self) -> int:
        return len(self._population)

    @property
    def generation(self) -> int:
        return 0

    def penalize(self, genome_id: int, amount: float | None = None) -> None:
        ...

    def quit_early(self) -> None:
        ...

    def remove(self, genome_id: int) -> None:
        ...

    def reward(self, genome_id: int, amount: float | None = None) -> None:
        ...

    def should_fly(
        self, genome_id: int, input_parameters: Iterable[float]
    ) -> bool:
        """Determine whether a bird should fly.

        :param genome_id: ID of the genome to evaluate.
        :param input_parameters: Parameters to use in the evaluation.
        :raises PopulationEmptyError: If the population is empty.
        :raises NetworkDoesNotExistError: If the network does not exist.
        :raises MissingConfigurationError: If activation function
        config is not found.
        """

        # Validate that the population is not empty.
        if not len(self):
            raise PopulationEmptyError(POPULATION_EMPTY_ERROR)

        # Get the network associated with the genome.
        try:
            phenotype: Phenotype = self._active_phenotypes[genome_id]
        except IndexError:
            raise NetworkDoesNotExistError(VOID_NETWORK_ERROR.format(genome_id))

        # Feed the input parameters through the associated network.
        determinant: float = phenotype.activate(input_parameters).pop()

        # Get the activation function in use.
        activation_function: str = self._neat_config.genome_config.__dict__.get(
            "activation_default"
        )

        # Get the activation function threshold.
        threshold: float = utils.get_config_value(
            self._game_config, f"ai.activation_thresholds.{activation_function}"
        )

        # Determine whether the bird should fly.
        return determinant >= threshold

    @staticmethod
    @abc.abstractmethod
    def should_quit() -> bool:
        ...

    def __load_config(self) -> neat.Config:
        """Load the configurations for the NEAT-AI."""

        return neat.Config(
            stagnation_type=neat.DefaultStagnation,
            reproduction_type=neat.DefaultReproduction,
            species_set_type=neat.DefaultSpeciesSet,
            genome_type=neat.DefaultGenome,
            filename=self.__CONFIG_PATH,
        )


@final
class NeatAITest(ABCNeatAI):
    """Representing the testing NEAT-AI in the game."""

    ########################
    ##   DUNDER METHODS   ##
    ########################

    def __init__(self, genomes: Sequence[Genotype], config: Config) -> None:
        """Initialize a NeatAITest instance."""

        super(NeatAITest, self).__init__(config)
        self._population: Sequence[Genotype] = genomes
        self._active_phenotypes: Sequence[Phenotype] = self.__init_phenotypes()

    ########################
    ##   PUBLIC METHODS   ##
    ########################

    @staticmethod
    def should_quit() -> bool:
        """Should this AI reset after every generation or not."""

        return True

    ########################
    ##   PUBLIC METHODS   ##
    ########################

    def __init_phenotypes(self) -> Sequence[Phenotype]:
        return [
            neat.nn.FeedForwardNetwork.create(genome, self._neat_config)
            for genome in self._population
        ]


@final
class NeatAITrain(ABCNeatAI):
    """Representing the training NEAT-AI in the game."""

    ########################
    ##   DUNDER METHODS   ##
    ########################

    def __init__(self, config: Config) -> None:
        """Initialize a NEAT-AI instance.

        :param config: Configuration mapping for the game.
        """

        LOGGER.operation("Initializing NeatAITrain instance")

        super().__init__(config)

        # Maintain a game instance.
        self.__game: src.objects.game.Game | None = None

        # Maintain sequences of active genotypes.
        self.__active_genotypes: list[Genotype] | None = None

        LOGGER.success("NeatAITrain instance initialized")

    def __len__(self) -> int:
        return (
            0
            if self.__active_genotypes is None
            else len(self.__active_genotypes)
        )

    ####################
    ##   PROPERTIES   ##
    ####################

    @property
    def generation(self) -> int:
        """Return the current generation number."""

        return self._population.generation

    ########################
    ##   PUBLIC METHODS   ##
    ########################

    def penalize(self, genome_id: int, amount: float | None = None) -> None:
        """Penalize a genome.

        :param genome_id: ID of the genome to penalize.
        :param amount: The amount to penalize by.
        :raises PopulationEmptyError: If the population is empty.
        :raises GenomeDoesNotExistError: If the genome does not exist.
        :raises MissingConfigurationError: If penalty config is not found.
        """

        # Validate that the population is not empty.
        if not len(self):
            raise PopulationEmptyError(POPULATION_EMPTY_ERROR)

        # Get amount from config if amount is None.
        if amount is None:
            amount = utils.get_config_value(self._game_config, "ai.penalty")

        # Penalize genome.
        try:
            self.__active_genotypes[genome_id].fitness -= amount
        except IndexError:
            raise GenomeDoesNotExistError(VOID_GENOME_ERROR.format(genome_id))

    def quit_early(self) -> None:
        """Quit training early."""

        self._population.config.no_fitness_termination = False
        self._population.config.fitness_threshold = 0

    def remove(self, genome_id: int) -> None:
        """Remove genome and the associated network from current generation.

        :param genome_id: ID of the genome to remove.
        :raises PopulationEmptyError: If the population is empty.
        :raises GenomeDoesNotExistError: If the genome does not exist.
        :raises NetworkDoesNotExistError: If the network does not exist.
        """

        # Validate that the population is not empty.
        if not len(self):
            raise PopulationEmptyError(POPULATION_EMPTY_ERROR)

        # Remove genotype from current generation.
        try:
            self.__active_genotypes.pop(genome_id)
        except IndexError:
            raise GenomeDoesNotExistError(VOID_GENOME_ERROR.format(genome_id))

        # Remove genotype from current generation.
        try:
            self._active_phenotypes.pop(genome_id)
        except IndexError:
            raise NetworkDoesNotExistError(VOID_NETWORK_ERROR.format(genome_id))

    def reward(self, genome_id: int, amount: float | None = None) -> None:
        """Reward a genome.

        :param genome_id: ID of the genome to reward.
        :param amount: The amount to reward with.
        :raises PopulationEmptyError: If the population is empty.
        :raises GenomeDoesNotExistError: If the genome does not exist.
        :raises MissingConfigurationError: If reward config is not found.
        """

        # Validate that the population is not empty.
        if not len(self):
            raise PopulationEmptyError(POPULATION_EMPTY_ERROR)

        # Get amount from config if amount is None.
        if amount is None:
            amount = utils.get_config_value(self._game_config, "ai.reward")

        # Reward genome.
        try:
            self.__active_genotypes[genome_id].fitness += amount
        except IndexError:
            raise GenomeDoesNotExistError(VOID_GENOME_ERROR.format(genome_id))

    @staticmethod
    def should_quit() -> bool:
        """Should this AI reset after every generation or not."""

        return False

    def train(self, game: src.objects.game.Game) -> None:
        """Train the AI on the game.

        :raises MissingConfigurationError: If maximum generation config
        is not found.
        """

        LOGGER.operation("Initializing training sequence")

        # Set the game instance.
        self.__game = game

        # Get the maximum number of generations.
        max_generations: int = utils.get_config_value(
            self._game_config, "ai.max_generations"
        )

        # Generate the population.
        self.__generate()

        # Train the population.
        best_genome: Genotype = self._population.run(
            fitness_function=self.__fitness_function, n=max_generations
        )

        file = utils.get_config_value(self._game_config, "ai.best_model_file")
        with open(file, "wb") as stream:
            pickle.dump(best_genome, stream)

        LOGGER.success("Training sequence completed")

    #########################
    ##   PRIVATE METHODS   ##
    #########################

    def __fitness_function(
        self, population: Sequence[tuple[int, Genotype]], config: neat.Config
    ) -> None:
        """Fitness function for the NEAT algorithm.

        :param population: The population of genomes.
        :param config: The AI configuration object.
        """

        self.__active_genotypes, self._active_phenotypes = [], []

        # Add references of the current population for the current generation.
        for _, genome in population:
            # Reset the fitness score for every member of the population.
            genome.fitness = 0.0

            # Add references to the genotype.
            self.__active_genotypes.append(genome)

            # Create a reference to a projected phenotype.
            self._active_phenotypes.append(Phenotype.create(genome, config))

        self.__game.play(random_seed=42)

    def __generate(self) -> None:
        """Generate a generation to prepare for a training session."""

        # Get filename for saved populations.
        save_file: str = utils.get_config_value(
            self._game_config, "ai.saved_population_file"
        )

        # Create reporters.
        stream_reporter: neat.StdOutReporter = neat.StdOutReporter(
            show_species_detail=True
        )
        checkpoint_reporter: neat.Checkpointer = neat.Checkpointer(
            generation_interval=1, filename_prefix=save_file
        )

        # Initialize the population.
        if saved := check_saved_population(self._game_config):
            LOGGER.info(f"Resuming training of population from {saved}")
            self._population = checkpoint_reporter.restore_checkpoint(saved)
        else:
            self._population = neat.Population(self._neat_config)

        self._population.add_reporter(stream_reporter)
        self._population.add_reporter(checkpoint_reporter)


def check_saved_population(config: Config) -> str:
    """Check for a saved population."""

    location, _ = utils.get_config_value(
        config, "ai.saved_population_file"
    ).split("/")

    path: pathlib.Path = pathlib.Path(location)

    if not path.is_dir() or not list(path.iterdir()):
        return ""

    else:
        return str(list(path.iterdir()).pop())
