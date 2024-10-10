from moea.utils import setup_spool_folder, setup_results_folder

from pymoo.core.mixed import MixedVariableGA
from pymoo.algorithms.moo.nsga2 import NSGA2


class BaseAlgorithm(NSGA2):

    def __str__(self) -> str:
        return self.__class__.__name__

    def _setup(self, problem, **kwargs):
        # Clean the spool and results folders
        setup_spool_folder()
        setup_results_folder()
        return super()._setup(problem, **kwargs)
