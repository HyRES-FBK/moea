from moea.utils import setup_spool_folder, setup_results_folder

from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.operators.mutation.pm import PM
from pymoo.operators.crossover.sbx import SBX
from pymoo.operators.survival.rank_and_crowding import RankAndCrowding


class BaseAlgorithm(NSGA2):

    def __init__(self, pop_size=100, **kwargs):
        super().__init__(
            pop_size,
            crossover=SBX(eta=10, prob=0.9),
            mutation=PM(eta=10, prob=1/7),
            survival=RankAndCrowding(),
            **kwargs
        )

    def __str__(self) -> str:
        return self.__class__.__name__

    def _setup(self, problem, **kwargs):
        # Clean the spool and results folders
        setup_spool_folder()
        setup_results_folder()
        return super()._setup(problem, **kwargs)
