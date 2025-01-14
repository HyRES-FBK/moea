from pymoo.operators.crossover.sbx import SBX

from moea.algorithms.base_algorithm import BaseAlgorithm
from moea.operators.domain_knowledge import DomainKnowledgeInitialization
from moea.operators.domain_knowledge import DKMutation


class Mahbub2016(BaseAlgorithm):

    def __init__(self,
                 pop_size=100,
                 sampling=DomainKnowledgeInitialization(betas=[2.0, 4.0]),
                 crossover=SBX(eta=10, prob=0.9),
                 mutation=DKMutation(eta=10, prob=0.1),
                 **kwargs):

        super().__init__(
            pop_size=pop_size,
            sampling=sampling,
            crossover=crossover,
            mutation=mutation,
            **kwargs)


if __name__ == '__main__':
    pass
