from moea.utils import setup_spool_folder, setup_results_folder

from pymoo.core.mixed import MixedVariableGA
from pymoo.util.display.multi import MultiObjectiveOutput
from pymoo.algorithms.moo.nsga2 import RankAndCrowding


class BaseAlgorithm(MixedVariableGA):

    def __init__(self,
                 pop_size=10,
                 survival=RankAndCrowding(),
                 output=MultiObjectiveOutput(),
                 **kwargs):
        super().__init__(pop_size=pop_size, survival=survival, output=output,
                         **kwargs)

    def __str__(self) -> str:
        return self.__class__.__name__

    def _setup(self, problem, **kwargs):
        # Clean the spool and results folders
        setup_spool_folder()
        setup_results_folder()
        return super()._setup(problem, **kwargs)
