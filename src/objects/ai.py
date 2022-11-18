"""This module contains the AI class."""

import neat

import src.objects.game
from src.enums import GameStateEnum
from src.utils.stenographer import Stenographer
from src.utils.types import *

LOGGER: Stenographer = Stenographer.create_logger()


class PopulationEmptyError(Exception):
    """Raise when operations are attempted on an empty population."""

    ...


class AI:
    """Representing the NEAT AI."""

    # Flight determinant threshold per activation function.
    __ACTIVATION_THRESHOLDS: dict[str, float] = {"tanh": 0.5}

    __CONFIG_PATH: str = "src/config/ai_config.cfg"
    __REWARD: int = 15
    __PENALTY: int = 100

    def __init__(self, game_config: Config) -> None:
        """Initialize an AI instance."""

        LOGGER.operation("Initializing AI")

        # Register configurations.
        self.__game_config: Config = game_config
        self.__ai_config: neat.config = self.__load_config()

        # Create the game instance for this session.
        self.__game: src.objects.game.Game = src.objects.game.Game(
            game_config=game_config, ai=self
        )

        # The active genomes and network in the current generation.
        self.__active_genotypes: list[neat.DefaultGenome] | None = None
        self.__active_phenotypes: list[neat.nn.FeedForwardNetwork] | None = None
        self.__current_generation: int = 0

        LOGGER.success("AI initialized")

    def __len__(self) -> int:
        return (
            0
            if self.__active_genotypes is None
            else len(self.__active_phenotypes)
        )

    def remove(self, genome_id: int) -> None:
        """Remove a genome and its network from the current generation."""

        # Validate that the population is not empty.
        if not len(self):
            raise PopulationEmptyError("Population is empty")

        # Remove genotype from current generation.
        try:
            self.__active_genotypes.pop(genome_id)
        except IndexError:
            raise ValueError(f"Genome with id {genome_id} does not exist")

        # Remove phenotype from current generation.
        try:
            self.__active_phenotypes.pop(genome_id)
        except IndexError:
            raise ValueError(f"Network with id {genome_id} does not exist")

    def should_fly(
        self, *, genome_id: int, input_parameters: Iterable[float]
    ) -> bool:
        """Determine whether the given bird should fly or not."""

        # Validate that the population is not empty.
        if not len(self):
            raise PopulationEmptyError("Population is empty")

        # Get the network associated with the current genome.
        phenotype: neat.nn.FeedForwardNetwork = self.__active_phenotypes[
            genome_id
        ]

        # Feed the input parameters through the associated network.
        determinant: float = phenotype.activate(input_parameters).pop()

        # Get the current activation function.
        activation_function: str = self.__ai_config.genome_config.__dict__[
            "activation_default"
        ]

        # Determine whether the bird should jump or not.
        return determinant >= self.__ACTIVATION_THRESHOLDS[activation_function]

    def penalize(self, genome_id: int, amount: float | None = None) -> None:
        """Penalize a genome."""

        if not len(self):
            raise PopulationEmptyError("Population is empty")

        self.__active_genotypes[genome_id].fitness -= amount or self.__PENALTY

    def reward(self, genome_id: int, amount: float | None = None) -> None:
        """Reward a genome."""

        if not len(self):
            raise PopulationEmptyError("Population is empty")

        self.__active_genotypes[genome_id].fitness += amount or self.__REWARD

    def train(self, max_generations: int = 30, verbose: bool = True) -> None:
        """Train the AI on the game."""

        # Create the population.
        population: neat.Population = neat.Population(self.__ai_config)

        # Add reporters if running in verbose mode.
        if verbose:
            stat_reporter: neat.StatisticsReporter = neat.StatisticsReporter()
            stream_reporter: neat.StdOutReporter = neat.StdOutReporter(
                show_species_detail=True
            )
            population.add_reporter(stat_reporter)
            population.add_reporter(stream_reporter)

        # Train the population.
        try:
            population.run(self.__fitness_function, max_generations)
        except KeyboardInterrupt:
            return

    def test(self) -> None:
        """Test the AI on the game."""

        raise NotImplemented

    def __fitness_function(
        self,
        population: Sequence[tuple[int, neat.DefaultGenome]],
        config: neat.Config,
    ) -> None:
        """This is the fitness function for the AI."""

        LOGGER.operation(f"Training generation {self.__current_generation:,}")

        # Add genomes and networks to current generation.
        self.__active_genotypes, self.__active_phenotypes = [], []
        for _, genome in population:
            # Set the initial fitness score for the genome.
            genome.fitness = 0.0

            # Create the neural network.
            network: neat.nn.FeedForwardNetwork = (
                neat.nn.FeedForwardNetwork.create(genome, config)
            )

            # Add the genome and its projected network to current generation.
            self.__active_genotypes.append(genome)
            self.__active_phenotypes.append(network)

        # Create a bird instances to represent the current genome.
        self.__game.add_bird(len(population))

        self.__game.state = GameStateEnum.PLAYING

        try:
            self.__game.play()
        except KeyboardInterrupt:
            pg.quit()
            raise

        LOGGER.success(f"Generation {self.__current_generation:,} trained")

        # Increment the generation counter.
        self.__current_generation += 1

    def __load_config(self) -> neat.Config:
        """Load the configurations for the AI."""

        return neat.Config(
            stagnation_type=neat.DefaultStagnation,
            reproduction_type=neat.DefaultReproduction,
            species_set_type=neat.DefaultSpeciesSet,
            genome_type=neat.DefaultGenome,
            filename=self.__CONFIG_PATH,
        )
