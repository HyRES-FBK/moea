from moea.config import logger
from moea.algorithms.base_algorithm import BaseAlgorithm
from moea.operators.domain_knowledge import DomainKnowledgeInitialization


class Mahbub2016(BaseAlgorithm):

    def __init__(self,
                 pop_size=100,
                 sampling=DomainKnowledgeInitialization(
                    betas=[2.0, 3.0, 4.0],
                 ),
                #  mutation=PM(eta=20),
                 **kwargs):

        super().__init__(
            pop_size=pop_size,
            sampling=sampling,
            # mutation=mutation,
            **kwargs)



if __name__ == '__main__':
    pass
